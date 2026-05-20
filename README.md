# Iyrin diagnostic daemons

Iyrin are my suite of critical power event diagnostic daemons

From the Aramaic עִיר ʿiyr, plural עִירִין ʿiyrin, referring to the angel "Watchers", these daemons are built to watch themselves - and your laptop - die.
Implementing a circular buffer in their logfiles, they aggressively poll the power state of the device and record what they see up to the moment of power failure, to aid in diagnosing the causes of my, and hopefully your, laptop problems.

## Why?

I do most of my work on a Lenovo T460 Thinkpad, which was originally released in 2016. Due to age and problems with Windows, in 2025 I switched to running Ubuntu and started performing maintenance on the device. However, due to financial and availability reasons, I had to use 3rd party replacements for the power supply port and batteries.
While my laptop was useable again, it began experiencing a number of problems, namely losing power with no warning despite reporting perfectly normal charge and voltage levels.
Out of frustration and a need to have a functioning laptop, I decided that the best course of action was to come up with a way to record the symptoms I was experiencing to diagnose the causes.
Unfortunately because of the way the first one I made works, there's actually measurable lag in the timestamps, so keeping the data being logged lightweight is the name of the game when I'm trying to record events that, from a user perspective, happen instantaneously. Therefore, from the initial Iyr "VC" I plan to create a small suite of related daemons that continuously log one or two parameters at a time, to expand their diagnostic capabilities.

## Iyr "VC"

- Aggressively logs battery Voltage and Charge percentage
- Records events - power rail voltage bleed, AC power status change, sudden changes in reported battery percentage
- Benchmark events - every 300 seconds records AC power status and voltage of batteries 0 and 1

## Iyr "AW"

- Aggressively logs battery Amps and Watts (updated - now knows what a milliamp is)
- Records Events - none currently
- Benchmark Events - every 300 seconds records amps and watts for batteries 0 and 1 (updated - now knows what a milliamp is)
