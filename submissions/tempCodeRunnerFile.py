from ping_game_theory import Strategy, StrategyTester, History, HistoryEntry, Move
import random, math

class Bot(Strategy):
    def __init__(self) -> None:
        self.author_netid = "hb969@snu.edu.in"
        self.strategy_name = "Adaptive Classifier with Forgiveness"
        self.strategy_desc = (
            "Starts cooperative, classifies opponent behavior (TFT, Pavlov, Cooperator, Defector, Noisy) "
            "and adapts: cooperates with reciprocators, exploits pure cooperators sparingly, defects vs pure defectors, "
            "and uses forgiveness for noise. Ends with final-round defection."
        )

        # Tunable parameters
        self.burn_in = 10
        self.min_samples_for_classify = 30
        self.exploit_rate = 0.005
        self.probe_rate = 0.002
        self.forgiveness_thresh = 0.05

    def begin(self) -> Move:
        return Move.COOPERATE

    def _extract_pairs(self, history: History):
        pairs = []
        for h in getattr(history, "entries", history):
            my = getattr(h, "my_move", None) or getattr(h, "self", None)
            opp = getattr(h, "opponent_move", None) or getattr(h, "other", None)
            if my and opp:
                pairs.append((my, opp))
        return pairs

    def _analyze(self, pairs):
        n = len(pairs)
        if n < 2: 
            return {"n": n, "opp_coop": 1.0}
        opp_coop = sum(1 for _, o in pairs if o == Move.COOPERATE) / n
        copy_rate = sum(1 for i in range(1, n) if pairs[i][1] == pairs[i-1][0]) / (n-1)
        repeat_rate = sum(1 for i in range(1, n) if pairs[i][1] == pairs[i-1][1]) / (n-1)
        return {"n": n, "opp_coop": opp_coop, "copy": copy_rate, "repeat": repeat_rate}

    def _classify(self, s):
        if s["n"] < self.min_samples_for_classify: return "UNKNOWN"
        if s["opp_coop"] > 0.98: return "COOP"
        if s["opp_coop"] < 0.05: return "DEFECT"
        if s["copy"] > 0.85: return "TFT"
        if s["repeat"] > 0.8: return "PAVLOV"
        return "NOISY"

    def turn(self, history: History) -> Move:
        pairs = self._extract_pairs(history)
        t = len(pairs)
        if t == 9999:  # last round (10,000 total)
            return Move.DEFECT
        if t < self.burn_in:
            return Move.COOPERATE

        s = self._analyze(pairs)
        c = self._classify(s)

        last_my, last_opp = pairs[-1]
        forgive = random.random() < self.forgiveness_thresh

        if c == "UNKNOWN":
            return Move.COOPERATE if last_opp == Move.COOPERATE else Move.DEFECT

        if c == "COOP":
            # exploit rarely
            if random.random() < self.exploit_rate:
                return Move.DEFECT
            return Move.COOPERATE

        if c == "DEFECT":
            return Move.DEFECT

        if c == "TFT":
            if last_opp == Move.DEFECT:
                return Move.DEFECT
            if random.random() < self.probe_rate:
                return Move.DEFECT
            return Move.COOPERATE

        if c == "PAVLOV":
            if last_my == Move.COOPERATE and last_opp == Move.COOPERATE:
                return Move.COOPERATE
            if last_opp == Move.DEFECT:
                return Move.DEFECT
            if random.random() < self.probe_rate:
                return Move.DEFECT
            return Move.COOPERATE

        if c == "NOISY":
            if forgive: 
                return Move.COOPERATE
            recent = pairs[-50:] if len(pairs) > 50 else pairs
            opp_def = sum(1 for _, o in recent if o == Move.DEFECT) / len(recent)
            return Move.COOPERATE if opp_def < 0.3 else Move.DEFECT

        return Move.COOPERATE


# Run simulation
if __name__ == "__main__":
    tester = StrategyTester(Bot)
    tester.run()
