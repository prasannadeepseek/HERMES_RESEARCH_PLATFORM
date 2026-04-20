import vectorbt as vbt
import pandas as pd
import numpy as np

# Create dummy data
df = pd.DataFrame({"close": np.random.randn(100) + 100})

try:
    print("Testing BBANDS...")
    # This is what the AI tried:
    # bb = vbt.BBANDS.run(df['close'], length=20, std=2)
    
    # This is the likely correct version:
    bb = vbt.BBANDS.run(df['close'], window=20, std=2)
    print("BBANDS success!")
except Exception as e:
    print(f"BBANDS failed: {e}")

try:
    print("\nTesting MA...")
    ma = vbt.MA.run(df['close'], window=20)
    print("MA success!")
except Exception as e:
    print(f"MA failed: {e}")
