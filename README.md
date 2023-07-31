# RepeRtition - a chess engine that helps you memorize your own chess repertoire using spaced repetition

RepeRtition plays moves from your own chess repertoire, using spaced repetition to help you memorize all variations. When "out of prep", it bridges to an external engine of your choice to continue the game.

This engine can be used to create a lichess.org bot in combination with [lichess-bot](https://github.com/ShailChoksi/lichess-bot). (Currently, only a subset of the UCI protocol is implemented, so lichess-bot is the only supported frontend.)

## Set up RepeRtition

1. Create the directory **~/.repertition/repertoire** with two subdirectories: **white** and **black**.
2. Populate **white** and **black** with one or more PGN files containing your opening repertoire for the corresponding color. (Note: It's possible to add and remove files and variations later.)
3. Create **~/.repertition/engine**, which must be an executable implementing an UCI engine (e.g., a symlink to /usr/bin/stockfish or a script executing [andoma](https://github.com/healeycodes/andoma)).
4. Run **pip install -r requirements.txt** (in a virtual environment, preferably).
5. Optional: You can edit **review_config.py** to change the default review intervals.
6. Optional: Test it by running **python repertition.py** and typing **go\<enter\>**. It should output the number of moves to review and the move to play. Type **quit\<enter\>**.

## Set up lichess-bot

1. Set up [lichess-bot](https://github.com/ShailChoksi/lichess-bot). Follow its documentation to create a lichess bot. Make sure you can play against it before continuing.
2. Currently, to be able to write to the chat, RepeRtition has to be added as a "homemade" engine. To do that, do: **ln -s <path/to/repertition> && echo -e '\nfrom repertition.lichess_bot_engine.engine import Repertition' >> strategies.py**
3. Open **config.yml** and edit the following settings:
   * name: "Repertition"
   * protocol: "homemade"
   * ponder: false
   * accept\_bot: false
   * max\_base: 10800
   * comment out "- rated" (do not accept rated games)
   * uncomment "allow\_list" and add your lichess user name

## Alternative user moves

In positions where it's the user's turn to move, only the main move is accepted. Any variations existing in the repertoire for those positions are ignored. If such position exists in multiple input PGN files, only the first responding move found is considered. **This also applies to the initial position!** That means that e.g., playing both d4 and e4 as white is not supported (but you could set up multiple bots or engine instances with different repertoires).

## TO DO

* Support any frontend (improve UCI implementation).
* Forward UCI options to bridged engine.
* Get rid of "homemade" lichess-bot engine, make writing to lichess chat work in UCI mode. Requires support from lichess-bot; e.g. forwarding a special UCI info message type or stderr to chat.
* Support alternative user moves. (Difficult concept, user cannot know which moves need review, etc.)
* Support multiple players with own repertoires.
