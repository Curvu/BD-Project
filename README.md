# Oblivion Sound
TODO: Write the project description

## Main Operations:
* ### **Administrator**
  - Create artist accounts
  - Create pre-paid cards (10, 25 or 50)
* ### **Consumer**
  - #### Consumer w/o subscription
    - Create their account
    - Buy a pre-paid card
    - Buy a subscription (month, quarter or semester)
  - #### Consumer w/ subscription
    - Create playlists (public or private)
    - Add songs to their playlists
    - Remove songs from their playlists
    - Access their private playlists
    - Update their playlist name
    - Delete their playlists
  - #### Both
    - Comment on songs or on another comments
    - Access to all songs, albums and public playlists
    - Have a playlist with their top 10 most played songs (last 30 days)
    - Update and delete their account
* ### **Artist**
  - Create albums
  - Create songs
  - Update their account information

## Potential concurrency conflicts:
- Creating a new account:
  - The same username can't be used twice
- Simultaneous comments:
  - Multiple comments at the same time can cause the comments to be out of order or to be with the wrong content
- Simultaneous subscriptions and pre-paid cards
- Simultaneous playlist creation, update and deletion
- Simultaneous song creation, update and deletion
- Simultaneous album creation, update and deletion

## Entities and their attributes:
- TODO: Write the entities and their attributes

<br>
<br>
<br>
<br>
<br>

## Authors:
- André Rodrigues Bettencourt Justo Louro
  - **CHANGEME**
- Filipe Alexandre Rodrigues
  - filiperodrigues@student.dei.uc.pt
- Joás Davi Duarte Silva
  - **CHANGEME**