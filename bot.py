import discord
from discord.ext import commands

from dotenv import load_dotenv
import re, json, os
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
EXERCISES_FILE = SCRIPT_DIR / "../registry/exercises.json"

exercises = []
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content

bot = commands.Bot(command_prefix="!", intents=intents)

load_dotenv()
TOKEN = os.getenv("TOKEN")

@bot.command(name="workout")
async def log_workout(ctx, *, workout_text):
    """
    User sends their workout as text after !workout
    Example: !workout Overhead Press: 2x8 60.1kg, Assisted Pullup: 1x8 60kg
    """
    try:
        # Use your existing parsing code here
        profile = resolve_workout(workout_text)  # returns user dict with appended workout
        save_workout(profile)                    # writes JSON to disk
        
        await ctx.send(f"Workout saved for {profile['username']}! ✅")
    except Exception as e:
        await ctx.send(f"Error parsing workout: {e}")

@bot.command(name="lastworkout")
async def last_workout(ctx):
    """
    Sends the last workout entry for a given user.
    """
    try:
        user = retrieve_user()
        with open(f"workouts_{user.lower()}.json", "r") as f:
            profile = json.load(f)
            
        workouts = profile.get("workouts", [])
        if not workouts:
            await ctx.send(f"No workouts found for {user}.")
            return

        last = workouts[-1]
        msg = f"Last workout for {user}:\n**{last['workout_name']}** on {last['date']}\n"
        for ex in last["exercises"]:
            sets_str = ", ".join([f"{s['reps']}x{s['weight']}" for s in ex["sets"]])
            msg += f"- {ex['name']}: {sets_str}\n"

        await ctx.send(msg)

    except FileNotFoundError:
        await ctx.send(f"No file found for user {user}.")
        

def refresh_exercises_list():
    with open(EXERCISES_FILE) as f:
        global exercises
        exercises = json.load(f)
        
        
def find_exercise(name):
    print(f"MATCHING exercise {name.strip()}")
    # Prep
    refresh_exercises_list()
    cl_input = name.strip().lower()

    for ex in exercises:        
        canonical_name = ex["canonical_name"].lower() 
        
        # Check canonical "official" name
        if canonical_name == cl_input:
            print(f"FOUND MATCH with canonical name: {canonical_name.title()}")
            return ex
        
        # Check regex for common variations
        if re.match(ex["nickname_regex"], cl_input):
            print(f"FOUND MATCH with regex: {cl_input.title()} is a variation of {canonical_name.title()}")
            return ex
            
        # Check nicknames for specific names (optionally provided by user)
        for name in ex["nicknames"]:
            name = name.lower()
            # print(f"Checking if {name.title()} == {cl_input.title()}")
            if name == cl_input:
                print(f"FOUND MATCH with nickname: {name.title()} with canonical name {canonical_name.title()}")
                return ex


def resolve_set(unsep_sets):
    print(f"Trying to resolve unseparated sets: {unsep_sets}")
    sets = []
    idx = 0
    for set in unsep_sets:
        set = set.replace("kg", "")
        data = re.split(r"[x ]+", set)
        set_counter = data[0]
        set_rep = data[1]
        set_weight = data[2]
        for j in range(int(set_counter)):
            idx += 1
            set = []
            sets.append({
                "reps": int(set_rep),
                "weight": float(set_weight),
            })
    print(f"Finished separating sets, result: {sets}")
    return sets

 
def dissimilate_input(input):
    match = re.match(r"^(.*?)(\d.*)$", input)
    if not match:
        raise ValueError(f"Could not parse input: {input}")
    
    ex_name = match.group(1).replace(":", "").title().strip()  # Isolate name
    ex = find_exercise(ex_name)

    sets_str = match.group(2).strip()
    unsep_sets = [str for str in re.split(r"(?<=kg)\s*", sets_str) if str]    
    sets = resolve_set(unsep_sets)
    
    return ex, sets


def resolve_exercise(user_input):
    print(f"Trying to resolve user-input: {user_input}")
    ex, sets = dissimilate_input(user_input)
    print()
    uexs = ""
    if ex:
        uexs = {            
                "ex_id": ex["id"],
                "name": ex["canonical_name"],
                "sets": sets
            }
    return uexs


def resolve_workout(input):
    profile = get_user_file()
    workouts = profile["workouts"]
    exs = input.replace("\n", "").split(", ") 
    uexs = [resolve_exercise(ex) for ex in exs]
    
    workouts.append({
           "workout_name": f"Test Upper Day {datetime.now().strftime("%B %d, %Y")}",
        "date": f"{datetime.now().strftime("%a %H:%M, %B %d, %Y")}",
        "exercises": uexs 
    })
    return profile


def get_user_file():
    user = retrieve_user()
    with open(f"workouts_{user}.json", "r") as f:
        return json.load(f)


def retrieve_user():
    return "Raphael".lower()


def save_workout(uexs):
    user = retrieve_user()
    with open(f"workouts_{user}.json", "w") as f:
        json.dump(uexs, f, indent=2)
    return 
    
        
def main():
    refresh_exercises_list()
    user_input = "Machine row 2x8 56kg"
    uexs = resolve_workout(user_input)
    save_workout(uexs)


if __name__ == "__main__":
    main()
    
    
bot.run(TOKEN)