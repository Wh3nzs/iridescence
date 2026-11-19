import random

from Projectiles import CenterBeam, SineRainProjectile, DashAttack, SyringeAttack, PlasticWrapAttack


class DexterBattle:
    def __init__(self, arena, player_turn=None):
        self.arena = arena
        self.player_turn = player_turn

        # RANDOM ATTACKS - edit this list to choose the boss's random moves.
        # After the script, play 1-3 random combos per player turn based on boss HP.
        # A tuple here launches several attacks together, just like in self.attacks.
        self.random_moves = [

            (
                self.wrap_at("horizontal", y=30),
                self.wrap_at("vertical", x=30),
                self.dash_from(270, sprite="Knife.png"),
                self.dash_from(310, sprite="Knife.png"),
                self.dash_from(230, sprite="Knife.png"),

            ),
            (
                self.rain,
                self.wrap_at("horizontal", y=45),
                self.syringe(spin_time=1.5, spin_turns=1.5),


            ),

            (
                self.beam_at("horizontal", x=15),
                self.beam_at("horizontal", x=45),
                self.beam_at("vertical", x=15),
                self.beam_at("vertical", x=45),
                self.dash_from(45, sprite="Knife.png"),
                self.dash_from(135, sprite="Knife.png"),
                self.dash_from(240, sprite="Knife.png"),
                self.dash_from(310, sprite="Knife.png"),
            ),
            (
                self.beam_at("horizontal", x=10),
                self.beam_at("horizontal", x=20),
                self.beam_at("horizontal", x=30),
                self.beam_at("horizontal", x=40),
                self.beam_at("horizontal", x=50),

                self.beam_at("vertical", x=10),
                self.beam_at("vertical", x=20),
                self.beam_at("vertical", x=30),
                self.beam_at("vertical", x=40),
                self.beam_at("vertical", x=50),
            ),

            (
                self.syringe(spin_time=1.2),
                self.wrap_at("horizontal", y=30),
                self.wrap_at("vertical", x=30),
                self.beam_at("vertical", x=15),
                self.beam_at("vertical", x=45),

            ),
            (
                self.rain,
                self.syringe(spin_time=1.2),
                self.syringe(spin_time=1.7),

            ),
            (
                self.syringe(spin_time=1.2),
                self.wrap_at("horizontal", y=30),
                self.beam_at("vertical", x=10),
                self.beam_at("vertical", x=20),
                self.beam_at("vertical", x=30),
                self.beam_at("vertical", x=40),
                self.beam_at("vertical", x=50),
            ),

            (
                self.beam_at("vertical", x=10),
                self.beam_at("vertical", x=20),
                self.beam_at("vertical", x=30),
                self.beam_at("vertical", x=40),
                self.beam_at("vertical", x=50),
                self.beam_at("vertical", x=60),
                self.syringe(spin_time=2, spin_turns=2),
                self.beam_at("horizontal", y=10),
                self.beam_at("horizontal", y=20),
                self.beam_at("horizontal", y=30),
                self.beam_at("horizontal", y=40),
                self.beam_at("horizontal", y=50),
                self.beam_at("horizontal", y=60),
            ),
            (
                self.syringe(spin_time=1, spin_turns=2),
                self.syringe(spin_time=2, spin_turns=2),
                self.syringe(spin_time=3, spin_turns=2),
                self.syringe(spin_time=3.2, spin_turns=2),
                self.syringe(spin_time=3.5, spin_turns=2),
                self.syringe(spin_time=3.7, spin_turns=2),
                self.wrap_at("horizontal", y=30),
            ),
            (
                self.rain,
                self.wrap_at("vertical", y=15),
                self.wrap_at("vertical", y=45),

            ),
            (
                self.wrap_at("vertical", y=15),
                self.wrap_at("vertical", y=45),
                self.dash_from(90, sprite="Knife.png"),
                self.wrap_at("horizontal", y=15),
                self.wrap_at("horizontal", y=45),                       
            )
        ]

        # Each tuple launches together; the next wave waits for every attack.
        # Three player turns before the finale keep even perfect hits from
        # ending this test early (four critical hits defeat Dexter).
        self.attacks = [

            self.wrap_at("vertical", x=30),
            self.syringe(spin_time=1, spin_turns=2),
            self.rain,
            self.player_attack,

            (
                self.dash_from(45, sprite="Knife.png"),
                self.dash_from(130, sprite="Knife.png"),
                self.syringe(spin_time=.8, spin_turns=10),

            ),
            (
                self.rain,
                self.wrap_at("horizontal", y=50),
                self.syringe(spin_time=1.5, spin_turns=2),


            ),
            (
                self.beam_at("vertical", x=20),
                self.beam_at("vertical", x=40),
                self.beam_at("horizontal", y=30),
                self.beam_at("horizontal", y=40),
                self.syringe(spin_time=1, spin_turns=1),
            ),
            (
                self.beam_at("vertical", x=10),
                self.beam_at("vertical", x=20),
                self.beam_at("vertical", x=30),
                self.beam_at("vertical", x=40),
                self.beam_at("vertical", x=50),
            ),

            (
                self.wrap_at("horizontal", y=30),
                self.dash_from(45, sprite="Knife.png"),
                self.dash_from(130, sprite="Knife.png"),
                self.dash_from(240, sprite="Knife.png"),
                self.dash_from(315, sprite="Knife.png"),
                self.syringe(spin_time=0.8, spin_turns=1),
            )

        ]

        self.attack_index = 0
        self.active_attacks = []

    @property
    def finished(self):
        # Main.py ends the fight when the boss's HP reaches zero.
        return False

    def update(self, player, dt):
        if self.attack_index >= len(self.attacks):
            # Recheck boss health after each player turn. Each selected tuple
            # is one full combo, and combos play sequentially before the turn.
            health_fraction = (self.player_turn.hp / self.player_turn.maxHp
                               if self.player_turn is not None else 1.0)
            combo_count = 3 if health_fraction <= 0.30 else 2 if health_fraction <= 0.50 else 1
            self.attacks = [random.choice(self.random_moves) for _ in range(combo_count)]
            self.attacks.append(self.player_attack)
            self.attack_index = 0
        attack_started = not self.active_attacks
        if attack_started:
            step = self.attacks[self.attack_index]
            group = step if isinstance(step, tuple) else (step,)
            for start_attack in group:
                self.active_attacks.extend(start_attack(player))
            attack_started = bool(self.active_attacks)

        for attack in self.active_attacks:
            attack.update(player, dt)
        self.active_attacks = [a for a in self.active_attacks if not a.finished]
        if not self.active_attacks:
            self.attack_index += 1
        return attack_started

    def player_attack(self, player):
        if self.player_turn is not None:
            self.player_turn.start()
        return []

    def syringe(self, spin_time=0.8, spin_turns=2):
        def start(player):
            return [SyringeAttack(self.arena, spin_time, spin_turns)]
        return start

    def rain(self, player):
        return [RainAttack(self.arena)]

    def rain_with(self, sprite):
        def start(player):
            return [RainAttack(self.arena, sprite)]
        return start

    def beam_at(self, orientation, x=None, y=None, sprite=None):
        def start(player):
            return [CenterBeam(self.arena, orientation, x, y, sprite)]
        return start

    def dash_from(self, degrees, *other_degrees, sprite=None):
        def start(player):
            return [DashAttack(self.arena, player, angle, sprite)
                    for angle in (degrees, *other_degrees)]
        return start

    def wrap_at(self, orientation="horizontal", x=None, y=None,
                width=12, roll_time=1.0, hold_time=2.0, warning_time=0.8):
        """Offsets are measured from the arena's left/top, just like beam_at."""
        def start(player):
            return [PlasticWrapAttack(self.arena, orientation, x, y,
                                      width, roll_time, hold_time, warning_time)]
        return start

    def draw(self, surface):
        for attack in self.active_attacks:
            attack.draw(surface)


class RainAttack:
    lanes = (0.5, 0.2, 0.8, 0.35, 0.65, 0.2, 0.8, 0.35, 0.2, 0.8, 0.35)

    def __init__(self, arena, sprite=None):
        self.arena = arena
        self.sprite = sprite
        self.drops = []
        self.next_lane = 0
        self.cooldown = 0.0

    @property
    def finished(self):
        return self.next_lane == len(self.lanes) and not self.drops

    def update(self, player, dt):
        self.cooldown -= dt
        if self.next_lane < len(self.lanes) and self.cooldown <= 0:
            x = self.arena.left + round(self.lanes[self.next_lane] * self.arena.width)
            self.drops.append(SineRainProjectile(x, self.arena.top - 12, self.sprite))
            self.next_lane += 1
            self.cooldown += 0.2

        remaining = []
        for drop in self.drops:
            drop.update(dt)
            if drop.rect.colliderect(player.rect):
                player.takeDamage(drop.damage)
            elif drop.rect.top < self.arena.bottom:
                remaining.append(drop)
        self.drops = remaining

    def draw(self, surface):
        for drop in self.drops:
            drop.draw(surface)