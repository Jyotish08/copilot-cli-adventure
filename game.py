"""Neon Runner 2088 - a replayable cyberpunk terminal adventure."""

from dataclasses import dataclass, field
import random
import sys
import time


PRINT_DELAY = 0.012


@dataclass
class GameState:
    credits: int = 500
    health: int = 100
    trace: int = 0
    reputation: int = 0
    mission: int = 0
    inventory: list[str] = field(default_factory=lambda: ["Neural deck", "Med patch"])
    flags: set[str] = field(default_factory=set)

    def has_item(self, item: str) -> bool:
        return item in self.inventory

    def add_item(self, item: str) -> None:
        if not self.has_item(item):
            self.inventory.append(item)

    def use_med_patch(self) -> bool:
        if not self.has_item("Med patch") or self.health >= 100:
            return False
        self.inventory.remove("Med patch")
        self.health = min(100, self.health + 35)
        return True


def slow_print(text: str, delay: float = PRINT_DELAY) -> None:
    """Print text gradually, but remain easy to automate with a zero delay."""
    if delay <= 0:
        print(text)
        return
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def ask(prompt: str, options: tuple[str, ...]) -> str:
    """Keep asking until the player enters one of the displayed options."""
    valid = {option.lower() for option in options}
    while True:
        answer = input(prompt).strip().lower()
        if answer in valid:
            return answer
        slow_print(f"Enter one of: {', '.join(options)}")


def show_status(state: GameState) -> None:
    slow_print("\n--- RUN STATUS ---")
    slow_print(
        f"Health: {state.health}% | Trace: {state.trace}% | "
        f"Credits: {state.credits} | Reputation: {state.reputation}"
    )
    slow_print(f"Gear: {', '.join(state.inventory)}")


def recover(state: GameState) -> None:
    if state.use_med_patch():
        slow_print("[MED] Med patch applied. Health restored.")
    else:
        slow_print("[MED] No usable med patch available.")


def check_failure(state: GameState) -> bool:
    if state.health <= 0:
        slow_print("\n[FAIL] Your neural signal goes dark. The city claims another runner.")
        return True
    if state.trace >= 100:
        slow_print("\n[FAIL] Corporate ICE triangulates your position. There is nowhere left to run.")
        return True
    return False


def random_encounter(state: GameState) -> bool:
    encounter = random.choice(("patrol", "cache", "quiet"))
    if encounter == "patrol":
        slow_print("\n[WARNING] A patrol drone sweeps the alley with a retinal scanner.")
        choice = ask("Do you [hide] or [run]? ", ("hide", "run"))
        if choice == "hide":
            state.trace = max(0, state.trace - 10)
            slow_print("[STEALTH] You hold your breath until the drone moves on.")
        else:
            state.health -= 15
            state.trace += 12
            slow_print("[CHASE] You escape, but a stun round clips your shoulder.")
    elif encounter == "cache":
        state.credits += 150
        state.add_item("ICE breaker")
        slow_print("[CACHE] You find a dead drop: 150 credits and an ICE breaker.")
    else:
        slow_print("[QUIET] The rain masks your signal. The next move is yours.")
    return check_failure(state)


def breach_vault(state: GameState) -> bool:
    slow_print("\n[!] ICE intrusion alarm triggered. Megacorp defense bots deploy.")
    choice = ask(
        "Do you [emp] the counter-virus, [spoof] the bots, or [jackout]? ",
        ("emp", "spoof", "jackout"),
    )
    if choice == "emp":
        state.credits += 1000
        state.reputation += 2
        state.trace += 25
        slow_print("[SUCCESS] The virus executes cleanly. The vault spills its secrets.")
    elif choice == "spoof":
        state.add_item("Corp credentials")
        state.reputation += 3
        state.trace += 10
        slow_print("[GHOST] You make the bots salute your forged identity.")
    else:
        state.health -= 30
        slow_print("[FAIL] Disconnect shock fries part of your deck.")
    return check_failure(state)


def network_recon(state: GameState) -> bool:
    slow_print("\n[+] Passive scan: an unpatched backdoor is listening on port 8080.")
    choice = ask(
        "Do you [reroute] proxy nodes, [trojan] the listener, or [probe] deeper? ",
        ("reroute", "trojan", "probe"),
    )
    if choice == "reroute":
        state.reputation += 2
        state.trace = max(0, state.trace - 15)
        slow_print("[SHADOW] Monitors never see you. Root access is yours.")
    elif choice == "trojan":
        state.trace += 35
        state.add_item("Signal jammer")
        slow_print("[RISK] The honeypot notices the trojan, but you rip out a signal jammer.")
    else:
        state.trace += 20
        state.credits += 300
        slow_print("[DEEP SCAN] You uncover a payroll ledger worth 300 credits.")
    return check_failure(state)


def choose_mission(state: GameState) -> bool:
    state.mission += 1
    if state.mission == 1:
        slow_print("\n=== MISSION 1: THE CORP DRIVE ===")
        choice = ask(
            "Do you [decrypt] immediately or [recon] network traffic first? ",
            ("decrypt", "recon"),
        )
        if choice == "decrypt":
            return breach_vault(state)
        return network_recon(state)

    slow_print("\n=== MISSION 2: GHOST TRAIN ===")
    slow_print("A runaway maglev carries a memory shard that could expose the corporation.")
    choice = ask(
        "Do you [board] the train, [derail] its route, or [sell] the coordinates? ",
        ("board", "derail", "sell"),
    )
    if choice == "board":
        state.health -= 20
        state.credits += 900
        state.reputation += 3
        slow_print("[BOARDING] You seize the shard after a brutal fight in the service car.")
    elif choice == "derail":
        state.trace += 30
        state.credits += 1400
        state.reputation += 1
        slow_print("[SABOTAGE] The train vanishes into an abandoned tunnel. The shard is yours.")
    else:
        state.credits += 700
        state.reputation -= 1
        state.flags.add("sold_coordinates")
        slow_print("[DEAL] A fixer pays well, but your allies will remember the betrayal.")
    return check_failure(state)


def ending(state: GameState) -> None:
    slow_print("\n=== RUN COMPLETE ===")
    if state.reputation >= 5 and state.trace < 60:
        slow_print("LEGEND ENDING: The city names you the Shadow Architect.")
    elif state.credits >= 2500:
        slow_print("MERCENARY ENDING: You buy a new identity and disappear beyond the grid.")
    elif state.trace < 100:
        slow_print("SURVIVOR ENDING: You live to run another night.")
    slow_print(f"Final haul: {state.credits} credits | Reputation: {state.reputation}")


def play() -> None:
    state = GameState()
    slow_print("\n=== SYSTEM BOOT: NEON RUNNER 2088 ===")
    slow_print("You are Cipher, an elite data-runner in Neo-Kolkata.")
    slow_print("An encrypted corp drive blinks in the rain.")
    while state.mission < 2:
        show_status(state)
        if choose_mission(state):
            return
        if state.mission < 2 and random_encounter(state):
            return
        if state.mission < 2:
            choice = ask("Continue [run], use a [med] patch, or [quit]? ", ("run", "med", "quit"))
            if choice == "med":
                recover(state)
            elif choice == "quit":
                slow_print("You fade into the neon crowd. Run terminated.")
                return
    ending(state)


def start_game() -> None:
    while True:
        play()
        choice = ask("\nPlay again? [yes] or [no]: ", ("yes", "no"))
        if choice == "no":
            slow_print("Connection closed. Stay sharp, runner.")
            return


if __name__ == "__main__":
    start_game()
