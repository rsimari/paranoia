## Paranoia

# Paranoia is a multiplayer shooter game. 

- First start the game server by running "python server/server.py". 
- Then join a game as a player by running "python client.py" in the client/ directory. 

When you first join, if you are the first player you will have to wait for other players to join before the game starts. Once four players have joined the game will start. You win the game if you can destroy all of your opponents before they destroy you.

# Game Architecture

Paranoia runs a game server that accepts all player connections on an initial port. The server then assigns the player another port for the game data to flow on. Once the player is assigned an open port, the client launches the game and starts accepting data from the server. Whenever a player moves or any event happens the client sends data to the server and the server broadcasts the message to the rest of the players so that they can sync with all the screens. Finally when a player drops the connection, the server broadcasts a message to delete that player from all the players screens and it frees the port that it was using for another player. 

