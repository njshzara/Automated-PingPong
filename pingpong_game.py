import pygame
import random
import math
import time

# --- Constants ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
BACKGROUND_COLOR = (20, 20, 30)
PADDLE_COLOR = (200, 200, 210)
BALL_COLOR = (255, 80, 80)
LINE_COLOR = (60, 60, 70)
TEXT_COLOR = (220, 220, 220)

PADDLE_WIDTH = 15
PADDLE_HEIGHT = 120
BALL_RADIUS = 10

PADDLE_SPEED_BASE = 7
PADDLE_SPEED_ADAPTIVE_FACTOR = 0.08
PADDLE_MAX_SPEED = 15
PADDLE_SMOOTHING = 0.15

INITIAL_BALL_SPEED_X = 7
INITIAL_BALL_SPEED_Y = 7
# NEW/MODIFIED Constants for speed increase
BALL_SPEED_INCREASE_FACTOR = 1.08 # Increase speed by 8% each paddle hit

CENTER_LINE_WIDTH = 4
DASH_LENGTH = 10
DASH_GAP = 8

PANEL_HEIGHT = 100
PANEL_COLOR = (40, 40, 50)
PANEL_Y_POSITION = SCREEN_HEIGHT - PANEL_HEIGHT


# --- Game Classes ---

class Ball:
    def __init__(self):
        self.reset()
        self.last_interaction_time = time.time()

    def reset(self, going_left=None):
        """Resets the ball to the center with random initial direction."""
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2 - PANEL_HEIGHT // 2
        if going_left is None:
            going_left = random.choice([True, False])
        self.speed_x = INITIAL_BALL_SPEED_X * (-1 if going_left else 1)
        self.speed_y = random.uniform(-INITIAL_BALL_SPEED_Y * 0.7, INITIAL_BALL_SPEED_Y * 0.7)
        if abs(self.speed_y) < 1:
            self.speed_y = random.choice([-1, 1]) * INITIAL_BALL_SPEED_Y * 0.5
        self.last_interaction_time = time.time()


    def move(self, dt):
        """Updates ball position based on speed and delta time."""
        self.x += self.speed_x * dt * 60
        self.y += self.speed_y * dt * 60

    def draw(self, screen):
        pygame.draw.circle(screen, BALL_COLOR, (int(self.x), int(self.y)), BALL_RADIUS)

    def bounce(self, axis, paddle_impact_offset=0):
        """Handles bouncing off walls or paddles."""
        if axis == 'y':
            self.speed_y *= -1
            # Optional: Record wall bounce time if needed for more complex reaction tracking
            # self.last_interaction_time = time.time()

        elif axis == 'x': # Paddle collision
            self.speed_x *= -1 # Reverse horizontal direction

            # --- Apply angle change based on impact offset ---
            max_angle_influence = 0.75 # How much paddle hit location affects y-speed
            self.speed_y += paddle_impact_offset * abs(self.speed_x) * max_angle_influence # Use abs(speed_x) post-reversal

            # --- Increase speed after paddle hit (NEW) ---
            self.speed_x *= BALL_SPEED_INCREASE_FACTOR
            self.speed_y *= BALL_SPEED_INCREASE_FACTOR

            # Prevent vertical speed from being exactly zero
            if self.speed_y == 0:
                self.speed_y = math.copysign(0.1, self.speed_y) # Give it a tiny push


            # --- Record interaction time ---
            self.last_interaction_time = time.time()

    def get_rect(self):
        return pygame.Rect(self.x - BALL_RADIUS, self.y - BALL_RADIUS, BALL_RADIUS * 2, BALL_RADIUS * 2)

# --- Paddle Class (No changes needed here for this feature) ---
class Paddle:
    def __init__(self, x, player_id):
        self.player_id = player_id # 0 for left, 1 for right
        self.initial_x = x
        self.x = x
        self.y = SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2 - PANEL_HEIGHT // 2
        self.target_y = self.y + PADDLE_HEIGHT // 2 # Target center y
        self.speed = 0
        self.hits = 0
        self.misses = 0
        self.reaction_times = []
        self.last_move_initiation_time = 0
        self.is_reacting = False

    def draw(self, screen):
        pygame.draw.rect(screen, PADDLE_COLOR, (self.x, int(self.y), PADDLE_WIDTH, PADDLE_HEIGHT), border_radius=5)

    def move(self, dt):
        center_y = self.y + PADDLE_HEIGHT / 2
        difference = self.target_y - center_y
        adaptive_speed_boost = abs(difference) * PADDLE_SPEED_ADAPTIVE_FACTOR
        desired_speed = min(PADDLE_MAX_SPEED, PADDLE_SPEED_BASE + adaptive_speed_boost)
        move_amount = difference * PADDLE_SMOOTHING * dt * 60
        if abs(move_amount) > desired_speed * dt * 60:
           move_amount = math.copysign(desired_speed * dt * 60, move_amount)
        self.y += move_amount
        self.y = max(0, min(self.y, SCREEN_HEIGHT - PADDLE_HEIGHT - PANEL_HEIGHT))
        self.speed = move_amount / (dt * 60) if dt > 0 else 0

    def update_ai(self, ball):
        is_ball_coming_towards_paddle = (self.player_id == 0 and ball.speed_x < 0) or \
                                        (self.player_id == 1 and ball.speed_x > 0)
        if is_ball_coming_towards_paddle:
            if not self.is_reacting:
                 self.last_move_initiation_time = time.time()
                 self.is_reacting = True
            predicted_y = self._predict_ball_y(ball)
            reaction_fuzziness = random.uniform(-PADDLE_HEIGHT * 0.1, PADDLE_HEIGHT * 0.1)
            target_y_candidate = predicted_y + reaction_fuzziness
            current_center = self.y + PADDLE_HEIGHT / 2
            # Smooth the target setting itself slightly
            self.target_y = current_center + (target_y_candidate - current_center) * 0.85
        else:
            self.is_reacting = False
            center_screen_y = (SCREEN_HEIGHT - PANEL_HEIGHT) / 2
            # Move towards center more slowly when idle
            current_center = self.y + PADDLE_HEIGHT / 2
            self.target_y = current_center + (center_screen_y - current_center) * 0.05

        half_paddle = PADDLE_HEIGHT / 2
        self.target_y = max(half_paddle, min(self.target_y, SCREEN_HEIGHT - PANEL_HEIGHT - half_paddle))

    def _predict_ball_y(self, ball):
        # Check if ball is moving away horizontally - prediction not needed/reliable
        if (self.player_id == 0 and ball.speed_x > 0) or \
           (self.player_id == 1 and ball.speed_x < 0):
             return (SCREEN_HEIGHT - PANEL_HEIGHT) / 2 # Default to center if moving away

        if abs(ball.speed_x) < 0.1: # Avoid division by near-zero
            return ball.y

        # Predict time to reach paddle's front edge
        target_x = self.x + PADDLE_WIDTH if self.player_id == 0 else self.x
        time_to_reach = (target_x - ball.x) / ball.speed_x

        # If time is negative, ball is already past the paddle plane (shouldn't happen with is_ball_coming_towards_paddle check, but good failsafe)
        if time_to_reach < 0:
             time_to_reach = 0 # Predict current Y

        predicted_y = ball.y + ball.speed_y * time_to_reach

        # --- Account for potential top/bottom bounces ---
        effective_screen_height = SCREEN_HEIGHT - PANEL_HEIGHT
        time_remaining = time_to_reach
        current_y = ball.y
        current_speed_y = ball.speed_y

        # Simulate bounces iteratively until time runs out
        while time_remaining > 0:
            time_to_top_wall = float('inf')
            time_to_bottom_wall = float('inf')

            if current_speed_y < 0: # Moving up
                time_to_top_wall = (BALL_RADIUS - current_y) / current_speed_y
            elif current_speed_y > 0: # Moving down
                time_to_bottom_wall = (effective_screen_height - BALL_RADIUS - current_y) / current_speed_y

            time_to_wall = min(time_to_top_wall, time_to_bottom_wall)

            if time_to_wall < time_remaining:
                # Will hit a wall before reaching paddle's x-plane
                time_remaining -= time_to_wall
                current_y += current_speed_y * time_to_wall # Move to wall
                current_speed_y *= -1 # Bounce
                # Nudge away from wall slightly to prevent sticking in prediction
                current_y += current_speed_y * 0.001
            else:
                # Will reach paddle x-plane before hitting another wall
                predicted_y = current_y + current_speed_y * time_remaining
                time_remaining = 0 # Done simulating

        # Clamp final prediction to stay within bounds (just in case)
        predicted_y = max(BALL_RADIUS, min(predicted_y, effective_screen_height - BALL_RADIUS))
        return predicted_y


    def record_hit(self, ball_last_interaction_time):
        self.hits += 1
        if self.is_reacting:
             reaction = time.time() - ball_last_interaction_time # Time since last interaction
             # reaction = time.time() - self.last_move_initiation_time # Alt: Time since AI could see ball coming
             self.reaction_times.append(reaction)
             if len(self.reaction_times) > 50:
                 self.reaction_times.pop(0)

    def record_miss(self):
        self.misses += 1

    def get_accuracy(self):
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0

    def get_avg_reaction_time(self):
        return (sum(self.reaction_times) / len(self.reaction_times)) if self.reaction_times else 0

    def get_rect(self):
        return pygame.Rect(self.x, self.y, PADDLE_WIDTH, PADDLE_HEIGHT)

    def reset_stats(self):
        self.hits = 0
        self.misses = 0
        self.reaction_times = []

# --- Analytics Class (No changes needed here) ---
# ... (keep the Analytics class as it was)

# --- Main Game Function (No changes needed here) ---
# ... (keep the main function as it was)

# --- Need to add the Analytics and main function back if running standalone ---
# Make sure to include the Analytics class and the main() function from the
# previous response if you are running this as a complete script.

# --- Game Analytics ---
class Analytics:
    def __init__(self):
        self.font_small = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 60)
        self.player_wins = [0, 0] # Wins for Player 0 (Left), Player 1 (Right)
        self.total_rounds = 0

    def increment_win(self, player_id):
        self.player_wins[player_id] += 1
        self.total_rounds += 1

    def get_win_ratio(self, player_id):
        return (self.player_wins[player_id] / self.total_rounds * 100) if self.total_rounds > 0 else 0

    def draw_panel(self, screen, paddles, scores, ball):
        # Draw Panel Background
        panel_rect = pygame.Rect(0, PANEL_Y_POSITION, SCREEN_WIDTH, PANEL_HEIGHT)
        pygame.draw.rect(screen, PANEL_COLOR, panel_rect)
        pygame.draw.line(screen, LINE_COLOR, (0, PANEL_Y_POSITION), (SCREEN_WIDTH, PANEL_Y_POSITION), 2) # Top border

        # --- Scores ---
        score_text = f"{scores[0]}   -   {scores[1]}"
        score_surf = self.font_large.render(score_text, True, TEXT_COLOR)
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH / 2, PANEL_Y_POSITION + PANEL_HEIGHT / 3)) # Position score slightly higher
        screen.blit(score_surf, score_rect)

        # --- Ball Speed ---
        current_speed = math.sqrt(ball.speed_x**2 + ball.speed_y**2)
        speed_text = f"Ball Speed: {current_speed:.1f}"
        speed_surf = self.font_small.render(speed_text, True, TEXT_COLOR)
        speed_rect = speed_surf.get_rect(center=(SCREEN_WIDTH / 2, PANEL_Y_POSITION + PANEL_HEIGHT * 0.7))
        screen.blit(speed_surf, speed_rect)

        # --- Player 0 (Left) Stats ---
        p0 = paddles[0]
        p0_acc = f"Acc: {p0.get_accuracy():.1f}%"
        p0_rt = f"RT: {p0.get_avg_reaction_time()*1000:.0f}ms" # Reaction time in ms
        p0_win = f"Win: {self.get_win_ratio(0):.1f}%"

        p0_acc_surf = self.font_small.render(p0_acc, True, TEXT_COLOR)
        p0_rt_surf = self.font_small.render(p0_rt, True, TEXT_COLOR)
        p0_win_surf = self.font_small.render(p0_win, True, TEXT_COLOR)

        stats_y_pos = PANEL_Y_POSITION + PANEL_HEIGHT * 0.7 # Position stats lower
        screen.blit(p0_acc_surf, (20, stats_y_pos))
        screen.blit(p0_rt_surf, (160, stats_y_pos))
        screen.blit(p0_win_surf, (300, stats_y_pos))

        # --- Player 1 (Right) Stats ---
        p1 = paddles[1]
        p1_acc = f"Acc: {p1.get_accuracy():.1f}%"
        p1_rt = f"RT: {p1.get_avg_reaction_time()*1000:.0f}ms"
        p1_win = f"Win: {self.get_win_ratio(1):.1f}%"

        p1_acc_surf = self.font_small.render(p1_acc, True, TEXT_COLOR)
        p1_rt_surf = self.font_small.render(p1_rt, True, TEXT_COLOR)
        p1_win_surf = self.font_small.render(p1_win, True, TEXT_COLOR)

        screen.blit(p1_win_surf, (SCREEN_WIDTH - 150, stats_y_pos))
        screen.blit(p1_rt_surf, (SCREEN_WIDTH - 300, stats_y_pos))
        screen.blit(p1_acc_surf, (SCREEN_WIDTH - 440, stats_y_pos))

    def reset_round_stats(self, paddles):
        for paddle in paddles:
            paddle.reset_stats()


# --- Main Game Function ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Advanced AI Pong")
    clock = pygame.time.Clock()
    random.seed() # Initialize random number generator

    # --- Game Objects ---
    ball = Ball()
    paddles = [
        Paddle(30, 0),                         # Left Paddle (Player 0)
        Paddle(SCREEN_WIDTH - 30 - PADDLE_WIDTH, 1) # Right Paddle (Player 1)
    ]
    scores = [0, 0]
    analytics = Analytics()

    running = True
    last_time = time.time() # For delta time calculation

    while running:
        # --- Delta Time Calculation ---
        current_time = time.time()
        dt = current_time - last_time # Time elapsed since last frame
        last_time = current_time
        # Limit dt to prevent physics issues if game hangs
        dt = min(dt, 0.1) 

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # --- AI Updates ---
        for paddle in paddles:
            paddle.update_ai(ball)

        # --- Game Logic ---
        ball.move(dt)
        for paddle in paddles:
            paddle.move(dt)

        # --- Collision Detection ---
        ball_rect = ball.get_rect()
        effective_screen_height = SCREEN_HEIGHT - PANEL_HEIGHT

        # Ball with top/bottom walls
        if ball_rect.top <= 0 or ball_rect.bottom >= effective_screen_height:
            ball.bounce('y')
             # Adjust position slightly to prevent sticking
            if ball_rect.top <= 0:
                ball.y = BALL_RADIUS + 1
            if ball_rect.bottom >= effective_screen_height:
                ball.y = effective_screen_height - BALL_RADIUS - 1


        # Ball with paddles
        for i, paddle in enumerate(paddles):
            paddle_rect = paddle.get_rect()
            if ball_rect.colliderect(paddle_rect):
                # Check if ball is actually moving towards the paddle it hit
                # Prevents double hits or hits from behind
                 ball_moving_left = ball.speed_x < 0
                 paddle_is_left = i == 0

                 if ball_moving_left == paddle_is_left: # Collision is valid only if directions match
                    ball_center_y = ball.y
                    paddle_center_y = paddle.y + PADDLE_HEIGHT / 2
                    # Calculate normalized impact offset (-1 to 1)
                    impact_offset = (ball_center_y - paddle_center_y) / (PADDLE_HEIGHT / 2)
                    impact_offset = max(-1.0, min(1.0, impact_offset)) # Clamp offset

                    ball.bounce('x', impact_offset)
                    paddle.record_hit(ball.last_interaction_time)

                     # Move ball slightly out of paddle to prevent sticking
                    if paddle_is_left:
                         ball.x = paddle_rect.right + BALL_RADIUS + 1
                    else:
                         ball.x = paddle_rect.left - BALL_RADIUS - 1
                    break # Only handle collision with one paddle per frame


        # --- Scoring ---
        scored = False
        if ball_rect.left <= 0:
            scores[1] += 1 # Player 1 (Right) scores
            paddles[0].record_miss() # Player 0 (Left) missed
            analytics.increment_win(1)
            ball.reset(going_left=False) # Reset ball towards winner
            scored = True
        elif ball_rect.right >= SCREEN_WIDTH:
            scores[0] += 1 # Player 0 (Left) scores
            paddles[1].record_miss() # Player 1 (Right) missed
            analytics.increment_win(0)
            ball.reset(going_left=True) # Reset ball towards winner
            scored = True

        if scored:
            print(f"Score: {scores[0]} - {scores[1]}")
            # Optional: Reset paddle stats each round if desired
            # analytics.reset_round_stats(paddles)
            pass # Ball reset handles speed reset


        # --- Drawing ---
        screen.fill(BACKGROUND_COLOR)

        # Draw dashed center line
        line_y = 0
        while line_y < effective_screen_height:
            start_pos = (SCREEN_WIDTH // 2 - CENTER_LINE_WIDTH // 2, line_y)
            end_pos = (SCREEN_WIDTH // 2 - CENTER_LINE_WIDTH // 2, line_y + DASH_LENGTH)
            pygame.draw.line(screen, LINE_COLOR, start_pos, end_pos, CENTER_LINE_WIDTH)
            line_y += DASH_LENGTH + DASH_GAP

        # Draw game objects
        ball.draw(screen)
        for paddle in paddles:
            paddle.draw(screen)

        # Draw analytics panel
        analytics.draw_panel(screen, paddles, scores, ball)

        # --- Update Display ---
        pygame.display.flip()

        # --- Frame Rate Control ---
        clock.tick(60) # Aim for 60 FPS

    pygame.quit()

if __name__ == "__main__":
    main()