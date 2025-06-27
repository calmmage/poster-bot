
- [x] Queue component
  - [x] enable botspot mongodb
  - [x] enable botspot queue
  - [x] import botspot queue
  - [x] create botspot queue
  - [x] add item to botspot queue
  - [x] override botspot queue item type - pydantic whatever
    - [x] import
    - [x] inherit
    - [x] pass to constructor

- [ ] receive message from user handler
  - [ ] implementation 1: forward
  - [ ] implementation 2: manual sender - use 
  - [ ] bonus: use Mark's features - picture and title generation

- [ ] send message to channel handler

- [ ] Add title generation flow and picture generation flow
- [ ] Add formatting niceities
  - [ ] @author in the end?
  - [ ] Visual separators / highlights / pleasantries? 


## Phase 1 - save message to db

Seems done
Test? 

## Phase 2 - post message on a schedule
- post on a schedule
- 1) scheduler
- [ ] enable scheduler
- [ ] get scheduler
- [ ] ... scheduler mode - app config
- [ ] ... dev -> on period
- [ ] ... non-dev - on cron / ... regularly

## Phase 3 - reminders when queue is close to empty


## Misc / extra

- [x] add nice logger config
  - [x] find it. calmlib? botspot?
  - [x] setup_logger. init_logger. config_logger

## Dump ideas

- [ ] Notify the user when the post was posted
  - [x] Save user id to the queue? 
  - [ ] Save list of users and access it - from bot users (if bot user enabled)
  - [ ] Tell the user / log how many posts remain in the queue

- [ ] implement smart queue item picker


## Move all features to the Queue Manager component

1) Queue with / without repetition
  - add a switch as a queue config
  - save queue info to somewhere? (metadata)
  - get_random_item method (pop?)
  - with repetition: 
2) Queue with / without priority
3) 