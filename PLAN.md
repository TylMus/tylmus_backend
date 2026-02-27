## Tylmus — Project Plan



### What It Does

\*\*Tylmus\*\* is a daily word game where players are presented with 16 words and must find four groups of four words that share a common theme. The game updates every day with a new set of categories, ensuring all players see the same puzzle.



### Game Rules

- There are exactly four categories, each containing four words.

- Players select four words at a time and submit them as a guess.

- If the four words belong to the same category, that category is revealed and its words are removed from the board.

- If the guess is incorrect, a mistake is recorded (max 4 mistakes allowed).

- The game ends when all four categories are found (win) or after four mistakes (loss).



### User Flow (Frontend)

1\. User opens the web app.

2\. Frontend calls `GET /api/game` to fetch today's words, categories (hidden), and any previously found categories/mistakes from the user's cookie.

3\. Words are displayed in a shuffled grid.

4\. User clicks on words to select them (up to four).

5\. User clicks "Submit" to guess.

6\. Frontend sends selected words to `POST /api/check\_selection`.

7\. Backend responds with:

&nbsp;  - If correct: category name, color, and whether game is complete.

&nbsp;  - If incorrect: updated mistake count, optionally colors of selected words.

8\. Frontend updates UI: removes found words, shows category block, updates mistake counter, and displays a message.

9\. User can shuffle words or deselect all.

10\. Game state persists via cookies, so reloading keeps progress.



### API Endpoints (Backend)



| Method | Endpoint                 | Description                                                                 |

|--------|--------------------------|-----------------------------------------------------------------------------|

| GET    | `/api/game`              | Returns today's words, categories (with colors), found categories, mistakes. |

| POST   | `/api/check\_selection`   | Accepts a list of 4 words; returns validity, category details, updated state. |

| GET    | `/api/game\_status`       | Returns current progress (found categories, mistakes, game complete).        |

| GET    | `/api/daily\_info`        | Returns info about today's game (date, completion status, found count).      |

| POST   | `/api/reset\_progress`    | Resets user's progress for the current day.                                   |



### Configuration

All configuration is via environment variables (backend `.env`):



| Variable       | Required | Default | Description                             |

|----------------|----------|---------|-----------------------------------------|

| `DATABASE\_PATH`| No       | `wordsdb.db` | Path to SQLite database file.          |

| `CORS\_ORIGINS` | No       | \*       | Comma-separated allowed origins (for dev). |



Frontend uses `VITE\_API\_BASE\_URL` to point to the backend.



### Data Storage

- \*\*SQLite\*\* database (`wordsdb.db`) with two tables:

&nbsp; - `categories` (`category\_id`, `category\_name`)

&nbsp; - `words` (`word\_id`, `category\_id`, `word`)

- The database is seeded with Yakut-themed categories and words.



### Daily Game Generation

- Each day's game is deterministic based on the date (UTC).

- Categories are selected using a random seed derived from the date string.

- The same 4 categories are shown to all players on that day.

- Words are shuffled per request but the set is fixed for the day.



### Progress Tracking

- User progress (found categories, mistakes) is stored in a signed HTTP-only cookie.

- Cookie expires after 2 days, allowing the game to carry over if the user returns the same day.

- No server-side session storage; backend reads/writes progress from the cookie.



### Frontend Features

- Responsive grid of word cards.

- Category blocks with distinct colors (yellow, green, blue, purple).

- Visual feedback on selection, success, and mistakes.

- Shuffle button to randomize word order.

- Attempt history (shown as colored dots).

- Game over / win messages.



### Future Enhancements

- Leaderboard / statistics (requires backend database).

- Share results as emoji grid.

- User accounts instead of cookie-based progress.
