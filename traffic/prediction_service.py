from datetime import timedelta

from cameras.models import Camera

from .models import Traffic, TrafficPrediction


class PredictionInsufficientDataError(Exception):
    pass


def _kalman_filter(values, process_variance=1.0, measurement_variance=4.0):
    if not values:
        return 0.0

    estimate = float(values[0])
    error_estimate = 1.0

    for measurement in values[1:]:
        error_estimate += process_variance
        kalman_gain = error_estimate / (error_estimate + measurement_variance)
        estimate = estimate + kalman_gain * (float(measurement) - estimate)
        error_estimate = (1 - kalman_gain) * error_estimate

    return estimate


def _build_transition_matrix(records):
    state_order = [choice[0] for choice in Traffic.CongestionLevel.choices]
    state_index = {state: idx for idx, state in enumerate(state_order)}

    size = len(state_order)
    # Laplace smoothing avoids zero-probability transitions.
    counts = [[1.0 for _ in range(size)] for _ in range(size)]

    for prev, curr in zip(records, records[1:]):
        prev_idx = state_index[prev.congestion_level]
        curr_idx = state_index[curr.congestion_level]
        counts[prev_idx][curr_idx] += 1.0

    matrix = []
    for row in counts:
        row_sum = sum(row)
        matrix.append([value / row_sum for value in row])

    return state_order, state_index, matrix


def _clamp(value, lower, upper):
    return max(lower, min(upper, value))


def generate_prediction_for_camera(camera, horizon_minutes=5, min_samples=5):
    records = list(
        Traffic.objects.filter(camera=camera)
        .order_by('-measured_at')[:500]
    )
    records.reverse()

    if len(records) < min_samples:
        raise PredictionInsufficientDataError(
            f'At least {min_samples} traffic records are required for {camera.code}.'
        )

    latest = records[-1]
    state_order, state_index, matrix = _build_transition_matrix(records)
    current_state_index = state_index[latest.congestion_level]
    probabilities = matrix[current_state_index]

    predicted_state_index = max(range(len(probabilities)), key=lambda idx: probabilities[idx])
    predicted_state = state_order[predicted_state_index]
    confidence = round(probabilities[predicted_state_index] * 100.0, 2)

    expected_state_index = sum(idx * prob for idx, prob in enumerate(probabilities))
    state_delta = expected_state_index - current_state_index

    vehicle_series = [record.vehicle_count for record in records]
    speed_series = [record.avg_speed_kph for record in records]
    occupancy_series = [record.occupancy_percent for record in records]

    filtered_vehicle_count = _kalman_filter(vehicle_series, process_variance=1.5, measurement_variance=6.0)
    filtered_speed = _kalman_filter(speed_series, process_variance=2.0, measurement_variance=5.0)
    filtered_occupancy = _kalman_filter(occupancy_series, process_variance=1.2, measurement_variance=4.0)

    predicted_vehicle_count = int(round(_clamp(filtered_vehicle_count * (1 + 0.08 * state_delta), 0, 999999)))
    predicted_avg_speed = round(_clamp(filtered_speed * (1 - 0.06 * state_delta), 0, 300), 2)
    predicted_occupancy = round(_clamp(filtered_occupancy * (1 + 0.07 * state_delta), 0, 100), 2)

    transition_probabilities = {
        state: round(prob * 100.0, 2)
        for state, prob in zip(state_order, probabilities)
    }

    prediction = TrafficPrediction.objects.create(
        camera=camera,
        based_on_record=latest,
        predicted_for=latest.measured_at + timedelta(minutes=horizon_minutes),
        horizon_minutes=horizon_minutes,
        predicted_congestion_level=predicted_state,
        confidence=confidence,
        predicted_vehicle_count=predicted_vehicle_count,
        predicted_avg_speed_kph=predicted_avg_speed,
        predicted_occupancy_percent=predicted_occupancy,
        transition_probabilities=transition_probabilities,
    )

    return prediction


def generate_predictions_for_all_cameras(horizon_minutes=5, min_samples=5):
    predictions = []
    for camera in Camera.objects.filter(is_active=True):
        try:
            prediction = generate_prediction_for_camera(
                camera,
                horizon_minutes=horizon_minutes,
                min_samples=min_samples,
            )
            predictions.append(prediction)
        except PredictionInsufficientDataError:
            continue

    return predictions
