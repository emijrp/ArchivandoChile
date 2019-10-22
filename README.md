# WaybackCL

This bot allows to backup media (photos, videos) of [Twitter](https://twitter.com) posts, sending them to a [Telegram](https://telegram.org) Channel.

## Deployment

* Rename `config.json.sample` to `config.json` and complete with your Twitter and Telegram tokens and channels.
  * To get a Twitter Bot Token, first create a Twitter account and activate it with a phone number, then go to [Twitter Developer](https://developer.twitter.com) and apply for a Developer Account.
  * To get a Telegram Bot, start a conversation with [BotFather](https://t.me/botfather) and ask it to create a new bot. 
  * Set a Telegram Channel, Group or Conversation ID in `telegram.chatID` property of the config file. If the channel/group is public, you can use the public name, with a `@` prefixed. e.g: `@username`.
  * (Optional) define a list of admins in `admins` property of config file. The admins can use the commands defined in **commands** section.
* Add the bot created in the previous step to the group or channel.
* Run `bot.py` and hope for the best (jk).

## Some design decisions, explained

### Banning system

Currently, the system permabans users that spam the bot with queries. The code has hardcoded three variables related to the ban system, and the ban status is saved on `config.json` file.

It also is able to ban/unban the users using commands sent to the Telegram Bot. (TODO: write this better)

### When the bot backs up media?

The bot looks for three types of mentions:
- When a mention has media attached to the status update, it downloads that media.
- When a mention is a reply to a status that has media attached to it, it downloads that media.
- When a mention is a reply to a status that is a commented retweet to a status with media, it downloads that media. _(TODO: explain this better)_

## TO-DO
* Cache of tweets backed up.
* A more decent database.
* A more decent error handling code.
* Mutexes on config edition.
