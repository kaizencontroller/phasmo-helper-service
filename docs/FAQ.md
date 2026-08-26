# FAQ

## Is this tied to Streamer.bot?

No. Streamer.bot is the first `IChatProvider` adapter; command processing is provider-neutral.

## Which game build is supported?

Phasmophobia 0.19.0.0. The app includes Deildegast, the Willow Street rework, EMF Level 5 photo tracking, and the Prison, Brownstone High School, and Point Hope Restricted variants.

## Why does `Dildegeist` still work in chat?

The official ghost name is **Deildegast**. Common misspellings are aliases so viewer guesses are not lost.

## Where is investigation data stored?

Under `PHASMO_STATE_DIR`. Use a persistent Railway Volume in production.

## How do I update game content?

Edit the JSON registry, call the protected reload endpoint, and review the validation report. Invalid content is not activated.
