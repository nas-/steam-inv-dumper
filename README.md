# Steam inventory dumper

Various utilities to interact with steam market and game coordinator.

This was created mainly as a learning exercise,and should be used with care.


# Selling items
Program is able to sell items into steam market, keeping them at highest possible price while still being the lowest absolute price.

Logic is:

If I am not the owner of the lowest priced item, delist and relist another one.

Minimum price the bot will reprice an item is defined,and the bot will never place orders below the lowest specified price.

All sales are tracked into a database, allowing to see how much the items were sold for.

# Floats retrieval
The bot is able to pull the floats of the items from inspect link, or directly from a market page, and store them in a database for later use.


#Usage

An example config can be found in config.example.json. Duplicate it and rename it to config.json before filling.

Here are the parameters:

**apikey**: string. The apikey of the account which will sell the items. Can be found here https://steamcommunity.com/dev/apikey

**username**: string.Username of the account for login

**password**: string.Password of the account for login

**identity_secret** : string.Identity secret for steamguard

**shared_secret**: string.Shared secret for confirming listings

**steamid**: string. steamid64 can be found at sites like https://steamid.io/

**heartbeat_interval**: Integer. Interval for sending heartbeats log messages in seconds.

**market_sell_timeout**: Integer .Sell loop will be round at maximum every _market_sell_timeout_ seconds.

**use_cookies**: Bool, Whether to use previously saved cookies for logging in.

**debug**: bool. Whether to log debug messages or not.

**db_url**: string . sqlite database url. "sqlite:///sales.sqlite"

**items_to_sell**: dict, containing items to sell.

Keys are market hash names. Values is a dict containing quantity to
keep on sale (for example, 3 keeps 3 listings for that item) and Min Price.

<code>items_to_sell:{


"CS:GO Weapon Case 2": {


"quantity": 1,

"min_price": 20.40

}</code>

# floats

Specific config for pulling floats, all inside the float dictionary.

floats.timeout: int, timeout between requests to Game coordinator.

floats.retrieve_floats: bool, if false the GC connections are not even started

floats.refresh_game_files: bool, if refreshes and saves to disk game files (items_game,schema,items_game_cdn, and csgo_english)

floats.float_accounts: list of dict, each dict containing username and password of accounts for float retrievals.

<code>
"floats": {
"timeout": 2,
"retrieve_floats": false,
"refresh_game_files": false,
"float_accounts": [
  {
    "username": "",
    "password": ""
  },
</code>

# LICENSE

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.




