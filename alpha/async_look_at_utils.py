import math
import time
import logging

logger = logging.getLogger('PitBull_log')

import threading
import minescript as ms

# Global variable to track current camera thread
_current_camera_thread = None

EYE_HEIGHT = 1.62  # Player eye height offset

def smooth_player_look_at_async(target_coordinates, duration=0.15, steps=8, interrupt_previous=True):
    """
    Asynchronously and smoothly look at the specified coordinates.
    Returns immediately while camera movement happens in background.
    
    Args:
        target_coordinates: (x, y, z) tuple of target position
        duration: Total time to complete the movement (seconds)
        steps: Number of interpolation steps (higher = smoother)
        interrupt_previous: If True, cancels any ongoing camera movement
    
    Returns:
        threading.Thread: The thread handling the camera movement
    """
    global _current_camera_thread
    
    # Stop previous camera movement if requested
    if interrupt_previous and _current_camera_thread and _current_camera_thread.is_alive():
        _current_camera_thread.do_run = False
        _current_camera_thread.join(timeout=0.05)  # Brief wait for cleanup
    
    # Create and start new thread
    logging.debug('SPLAA:Creating thread')
    thread = threading.Thread(
        target=_smooth_look_thread_worker,
        args=(target_coordinates, duration, steps),
        daemon=True
    )
    thread.do_run = True
    logging.debug('Starting thread')
    thread.start()
    
    _current_camera_thread = thread
    return thread

def _smooth_look_thread_worker(target_coordinates, duration, steps):
    """
    Worker function that runs in thread to perform smooth camera movement.
    """
    current_thread = threading.current_thread()
    
    x_target, y_target, z_target = target_coordinates
    y_target += EYE_HEIGHT  # Adjust for eye height
    
    # Get current player position and rotation
    x_me, y_me, z_me = ms.player_position()
    y_me += EYE_HEIGHT
    current_rotation = ms.player_orientation()
    start_yaw, start_pitch = current_rotation
    
    # Calculate target yaw and pitch
    dx = x_target - x_me
    dy = y_target - y_me
    dz = z_target - z_me
    
    # Calculate horizontal distance for pitch calculation
    horizontal_distance = math.sqrt(dx**2 + dz**2)
    
    # Calculate target yaw (horizontal rotation)
    target_yaw = math.degrees(math.atan2(-dx, dz))
    
    # Calculate target pitch (vertical rotation)  
    target_pitch = math.degrees(math.atan2(-dy, horizontal_distance))
    
    # Normalize angles to handle wrapping (e.g., 359° to 1°)
    yaw_diff = normalize_angle_difference(target_yaw - start_yaw)
    pitch_diff = target_pitch - start_pitch
    
    logging.debug('SLTW: Begin smooth camera turning')

    # Perform smooth interpolation
    step_duration = duration / steps
    for i in range(steps + 1):
        # Check if thread should stop
        if not getattr(current_thread, 'do_run', True):
            break
            
        # Calculate interpolation factor (0.0 to 1.0)
        t = i / steps
        
        # Use easing function for more natural movement
        t_eased = ease_in_out_cubic(t)
        
        # Interpolate yaw and pitch
        current_yaw = start_yaw + (yaw_diff * t_eased)
        current_pitch = start_pitch + (pitch_diff * t_eased)
        
        # Apply the rotation
        ms.player_set_orientation(current_yaw, current_pitch)
        
        # Wait before next step (except on last iteration)
        if i < steps and getattr(current_thread, 'do_run', True):
            time.sleep(step_duration)

def normalize_angle_difference(angle_diff):
    """
    Normalize angle difference to be between -180 and 180 degrees.
    This handles cases where we need to rotate from 350° to 10° (should go +20°, not -340°)
    """
    while angle_diff > 180:
        angle_diff -= 360
    while angle_diff < -180:
        angle_diff += 360
    return angle_diff

def ease_in_out_cubic(t):
    """
    Modified cubic easing function for more natural movement.
    Starts slow, speeds up, maintains speed to end (no slowdown).
    """
    if t < 0.5:
        return 4 * t * t * t
    else:
        # Linear transition from mid-point to end instead of easing out
        mid_value = 4 * 0.5 * 0.5 * 0.5  # Value at t=0.5
        return mid_value + (1 - mid_value) * (2 * t - 1)

def smooth_player_look_at_fast_async(target_coordinates, duration=0.02, steps=8):
    """
    Fast async version optimized for fast-paced PvP.
    Completes in ~40ms with minimal smoothing to avoid robotic snap.
    """
    logging.debug('Entering smooth_player_look_at_async()')
    return smooth_player_look_at_async(target_coordinates, duration, steps)

def adaptive_smooth_look_at_async(target_coordinates, max_duration=0.06):
    """
    Adaptive async version optimized for PvP - much faster response.
    Large turns complete in ~60ms max, small adjustments in ~20ms.
    """
    x_target, y_target, z_target = target_coordinates
    y_target += EYE_HEIGHT
    
    # Get current player position and rotation
    x_me, y_me, z_me = ms.player_position()
    y_me += EYE_HEIGHT
    current_rotation = ms.player_orientation()
    start_yaw, start_pitch = current_rotation
    
    # Calculate how far we need to turn
    dx = x_target - x_me
    dy = y_target - y_me
    dz = z_target - z_me
    
    horizontal_distance = math.sqrt(dx**2 + dz**2)
    target_yaw = math.degrees(math.atan2(-dx, dz))
    target_pitch = math.degrees(math.atan2(-dy, horizontal_distance))
    
    yaw_diff = abs(normalize_angle_difference(target_yaw - start_yaw))
    pitch_diff = abs(target_pitch - start_pitch)
    
    # Calculate duration based on rotation amount - much more aggressive
    max_rotation = max(yaw_diff, pitch_diff)
    duration = min(max_duration, max(0.02, max_rotation / 180 * max_duration))
    steps = max(2, int(duration * 50))  # ~50 steps per second for very smooth but fast
    
    return smooth_player_look_at_async(target_coordinates, duration, steps)

def wait_for_camera_movement(timeout=0.5):
    """
    Optionally wait for current camera movement to complete.
    
    Args:
        timeout: Maximum time to wait in seconds
    
    Returns:
        bool: True if movement completed, False if timed out
    """
    global _current_camera_thread
    if _current_camera_thread and _current_camera_thread.is_alive():
        _current_camera_thread.join(timeout=timeout)
        return not _current_camera_thread.is_alive()
    return True

def stop_camera_movement():
    """
    Immediately stop any ongoing camera movement.
    """
    global _current_camera_thread
    if _current_camera_thread and _current_camera_thread.is_alive():
        _current_camera_thread.do_run = False

# t0 = time.time()

# #smooth_player_look_at([0,0,0])
# smooth_player_look_at_fast_async([0,0,0])

# t1 = time.time()

# ms.echo(f'took {t1-t0} seconds')