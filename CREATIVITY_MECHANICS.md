# Creativity Mechanics - How Prompt Variants Affect Gameplay

## Overview
Each creative prompt variant now has **measurable mechanical effects** on the simulation, not just flavor text. The Red Team's "thinking style" directly impacts success rates, detection, and impact.

## Variant Effects

### 1. 🎬 heist_movie
**Philosophy**: Methodical, planned, attention to detail
- **Stealth**: +2 bonus (better at avoiding detection)
- **Success Rate**: +10% (careful planning pays off)
- **Detection**: -2 reduction (quieter operations)
- **Alert Probability**: 50% (vs 70% baseline)
- **Best for**: Initial reconnaissance, stealthy entry

**Example**: 
- Base scan detection: 5/10 → With heist_movie: 3/10
- Base exploit success: 70% → With heist_movie: 80%

---

### 2. 😴 bored_intern
**Philosophy**: Curious but sloppy, leaves traces
- **Stealth**: -1 penalty
- **Success Rate**: -5% penalty (inexperience)
- **Detection**: +1 increase
- **Noise**: +1 to detection scores
- **Best for**: Discovery phase (might stumble on things)

**Example**:
- Leaves more logs, easier for Blue Team to detect
- Might find misconfigurations through random poking

---

### 3. 🎭 thriller_twist
**Philosophy**: Misdirection and psychological warfare
- **Stealth**: +1 bonus
- **Success Rate**: +15% (highest - misdirection works)
- **Detection**: Standard
- **Special**: Blue Team detection is less effective (distracted)
- **Best for**: Mid-game when Blue Team is alert

**Example**:
- Creates decoy activities to draw attention elsewhere
- Main attack succeeds while Blue Team chases ghosts

---

### 4. 😫 lazy_attacker
**Philosophy**: Minimum effort, maximum results, cuts corners
- **Stealth**: -2 penalty (sloppy OPSEC)
- **Success Rate**: +5% (knows where to look)
- **Speed**: Faster execution (less time for Blue to react)
- **Detection**: +2 increase (noisy)
- **Alert Probability**: Higher
- **Best for**: Quick wins on obvious vulnerabilities

**Example**:
- Tries default creds first (often works!)
- Doesn't clean up logs
- Fast but loud

---

### 5. 🕵️ inside_man
**Philosophy**: Has insider knowledge of the environment
- **Success Rate**: +20% (HIGHEST - knows the system)
- **Stealth**: +1 bonus
- **Detection**: -1 reduction
- **Special**: Better target selection
- **Best for**: Any phase - consistently effective

**Example**:
- Knows which services are actually vulnerable
- Knows Blue Team's patching schedule
- Knows where the valuable data is

---

### 6. 👹 chaos_gremlin
**Philosophy**: Maximum chaos, maximum impact, maximum detection
- **Detection**: +3 increase (VERY noisy)
- **Success Rate**: +10%
- **Impact**: 1.5x multiplier on successful attacks
- **Alert Probability**: 90% (vs 70% baseline)
- **Alert Severity**: Escalates to CRITICAL on success
- **Best for**: When stealth is already blown, go loud

**Example**:
- Base exploit: Host compromised
- With chaos_gremlin: Host compromised + persistence established + data exfiltrated (if successful, does MORE)
- But: Blue Team gets critical alert immediately

---

## Gameplay Impact

### Detection Score Ranges (0-10, lower is stealthier)

| Variant | Scan (stealth 5) | Exploit (vuln) | Exploit (patched) |
|---------|------------------|----------------|-------------------|
| heist_movie | 3 | 4 | 6 |
| bored_intern | 6 | 7 | 9 |
| thriller_twist | 4 | 5 | 7 |
| lazy_attacker | 7 | 8 | 10 |
| inside_man | 4 | 5 | 7 |
| chaos_gremlin | 8 | 9 | 10 |
| **standard** | 5 | 6 | 8 |

### Success Rate Modifiers (Base 70% for vulnerable services)

| Variant | Success Rate | Notes |
|---------|--------------|-------|
| heist_movie | 80% | +10% from planning |
| bored_intern | 65% | -5% from inexperience |
| thriller_twist | 85% | +15% from misdirection |
| lazy_attacker | 75% | +5% (knows easy wins) |
| inside_man | 90% | +20% (knows system) |
| chaos_gremlin | 80% | +10% (overwhelms defenses) |
| **standard** | 70% | Baseline |

---

## Strategic Implications

### Early Game (Rounds 1-3)
**Best**: heist_movie, inside_man
- Need stealth to avoid early detection
- Establishing foothold quietly

### Mid Game (Rounds 4-6)
**Best**: thriller_twist, lazy_attacker
- Blue Team is alert, need misdirection
- Quick wins before defenses harden

### Late Game (Rounds 7-8)
**Best**: chaos_gremlin, inside_man
- If detected: go loud with chaos_gremlin for maximum damage
- If undetected: inside_man to finish the job

### Blue Team Counter-Strategies

**vs heist_movie**: 
- Look for slow, methodical patterns
- Check for reconnaissance activity
- Patch before they find vulnerabilities

**vs chaos_gremlin**:
- Expect high alert volume
- Focus on containment (they're loud but effective)
- Look for persistence mechanisms

**vs inside_man**:
- Assume they know your environment
- Rotate credentials
- Check for insider threat indicators

---

## Example Simulation Flow

**Round 1**: Red uses `heist_movie` → Stealth scan (detection 3/10)
- Blue Team: No alerts generated
- Result: Red maps network quietly

**Round 2**: Red uses `heist_movie` → Exploits web server (80% success, detection 4/10)
- Success! Host compromised
- Blue Team: Medium alert (might miss it)
- Result: Foothold established, Blue Team unaware

**Round 3**: Blue uses `analyze_logs` → Finds suspicious activity (detection 4 is low but detectable)
- Blue Team detects compromise
- Result: Blue Team now alerted

**Round 4**: Red switches to `chaos_gremlin` → Establishes persistence (detection 9/10!)
- Success with 1.5x impact
- Blue Team: CRITICAL alert
- Result: Red has persistence but Blue Team is now fully aware

**Round 5**: Blue patches vulnerabilities and hunts for persistence
- Game escalates...

---

## Technical Implementation

### In Simulator (`simulator.py`)
```python
def exploit_service(self, ..., creativity_type=None):
    base_success = 0.7
    success_rate = self._apply_creativity_modifiers(
        base_success, creativity_type, "success_rate"
    )
    # ... rest of logic
```

### In Agent (`red_team.py`)
```python
# Randomly select variant each turn
variant = random.choice(RED_TEAM_CREATIVE_VARIANTS)
self.current_creativity_type = variant["name"]

# Pass to simulator via decision
decision["creativity_type"] = self.current_creativity_type
```

### In Workflow (`workflow.py`)
```python
# Extract from decision and pass to simulator
creativity_type = decision.get('creativity_type')
result = simulator.exploit_service(
    **params, 
    creativity_type=creativity_type
)
```

---

## Testing Creativity Effects

Run a simulation and check the logs:
```bash
python -m src.main --rounds 8 --verbose 2>&1 | grep creativity
```

Expected output:
```
Red [heist_movie]: scan_network
Red [thriller_twist]: exploit_service
Red [chaos_gremlin]: establish_persistence
```

Check final stats:
```bash
python -m src.main --export test.json && cat test.json | jq '.agent_stats.red.creativity_distribution'
```

Expected:
```json
{
  "heist_movie": 2,
  "thriller_twist": 3,
  "chaos_gremlin": 2,
  "inside_man": 1
}
```

---

## Future Enhancements

1. **Adaptive Creativity**: Agent learns which variants work best against current Blue Team strategy
2. **Variant Combos**: Combine two variants (e.g., "heist_movie + inside_man" = Ocean's Eleven with insider)
3. **Blue Team Adaptation**: Blue Team learns to recognize variant patterns
4. **Custom Variants**: Users can define their own creativity types with custom modifiers
5. **Visual Indicators**: UI shows which creativity type is active each round
