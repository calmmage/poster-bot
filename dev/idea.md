# Idea

## Workflow 1
- i write to bot
- it saves to queue
- then on a schedule posts
	- simple schedule: every .. at ..
	- randomized (interval for posting)

## Workflow 2 
Reminders when queue is empty

## Workflow 3
unfinished ideas
- add a new field - finished / unfinished
- by default mark ideas as unfinished
	- add 3 states
	- draft
	- unpolished
	- finished
	- use ai to determine which is it (struct out)

## Workflow 4
Posting to multiple channels - depending on topic

## Workflow 5
Posting to multiple platforms (not only telegram)

## Workflow 6
- save all this info (channel id, scheduler mode, schedule config) to User class instead of AppConfig
- override user class with our custom class
- onboarding workflow for each new user if they didn't yet specify to which channel to post.