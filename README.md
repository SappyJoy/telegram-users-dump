# telegram-users-dump

---

Utility to export `User Info` of telegram users from specified channel/chat.

## Usage

```sh
telegram_users_dump -c <chat_name> -p <phone_num> [-f <filter>] [-o <file>]

Where:
    -c,  --chat         Unique name of a channel/chat. E.g. @python.
    -p,  --phone        Phone number. E.g. +380503211234.
    -f,  --filter       Filter using regular expression
    -i,  --ignore_case  Ignore case while filtering
    -o,  --out          Output file name or full path. (Default: telegram_<chatName>.log)
    -e,  --exp          Exporter name. text | json | csv (Default: 'csv')
    -h,  --help         Show this help message and exit.
```
