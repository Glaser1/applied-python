import random
from functools import wraps

import bcrypt
import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import connection, cursor

load_dotenv()

"""
USERS:
id INT PK
username(login) VARCHAR(150) UNIQUE NOT NULL
first_name VARCHAR(150) NOT NULL
last_name VARCHAR(150) NOT NULL
password VARCHAR(255) NOT NULL
is_authorized BOOLEAN DEFAULT FALSE

POSTS:
id INT PK
title VARCHAR(150) NOT NULL
text TEXT NOT NULL

BLOGS:
id INT PK
title VARCHAR(150) NOT NULL
user_id INT FK NOT NULL,
is_deleted BOOL DEFAULT FALSE
UNIQUE (title, user_id)


BLOGS_POSTS: (secondary_table)
post_id INT FK
blog_id INT FK

COMMENTS:
id INT PK
text varchar(255) NOT NULL
user_id INT FK NOT NULL
post_id INT FK NOT NULL
parent_comment_id INT FK (self-reference)
"""


class Blog:
    def __init__(self, conn_params: dict[str, str]):
        self.conn: connection = psycopg2.connect(**conn_params)
        self._healthcheck()
        self._init_tables()
        self._create_indexes()

    @staticmethod
    def _check_password(self, input_password: str, hashed_password: str) -> bool:
        if bcrypt.checkpw(input_password.encode("utf-8"), hashed_password.encode("utf-8")):
            return True
        return False

    @staticmethod
    def with_cursor(func):
        @wraps(wrapped=func)
        def wrapper(self, *args, **kwargs):
            cur = None
            try:
                cur: cursor = self.conn.cursor()
                result = func(self, cur, *args, **kwargs)
                self.conn.commit()
                return result
            except Exception as e:
                print(f"Ошибка базы данных: {e}")
                self.conn.rollback()
            finally:
                if cur is not None:
                    cur.close()

        return wrapper

    @with_cursor
    def _healthcheck(self, cur: cursor):
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        print(f"Connected to: {db_version}")

    @with_cursor
    def _init_tables(self, cur: cursor):
        cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(150) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    first_name VARCHAR(150) NOT NULL,
                    last_name VARCHAR(150) NOT NULL,
                    is_authorized BOOLEAN NOT NULL DEFAULT FALSE
                );
            """)

        cur.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(150) NOT NULL,
                    text TEXT NOT NULL
                );
            """)
        cur.execute("""
                CREATE TABLE IF NOT EXISTS blogs (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(150) NOT NULL,
                    user_id INTEGER NOT NULL,
                    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                    CONSTRAINT fk_user
                        FOREIGN KEY(user_id)
                        REFERENCES users(id)
                        ON DELETE CASCADE,
                    UNIQUE (title, user_id)
                );
            """)
        cur.execute("""
                CREATE TABLE IF NOT EXISTS blogs_posts (
                blog_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
            
                PRIMARY KEY (blog_id, post_id),
                
                FOREIGN KEY (blog_id)
                    REFERENCES blogs(id)
                    ON DELETE CASCADE,
                    
                FOREIGN KEY (post_id)
                    REFERENCES posts(id)
                    ON DELETE CASCADE
            );
            """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id SERIAL PRIMARY KEY,
                text VARCHAR(150) NOT NULL,
                user_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
                parent_comment_id INTEGER,
                
                FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE CASCADE,

                FOREIGN KEY (post_id)
                        REFERENCES posts(id)
                        ON DELETE CASCADE,
                        
                FOREIGN KEY (parent_comment_id)
                    REFERENCES comments(id)
                    ON DELETE CASCADE
                );
        """)

    @with_cursor
    def _create_indexes(self, cur: cursor):
        # posts indexes
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_posts_title ON posts USING gin (title gin_trgm_ops);")

        # blogs indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_blogs_title ON blogs USING gin (title gin_trgm_ops);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_blogs_user_id ON blogs(user_id);")

        # blogs_posts indexes
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_blogs_posts_blog_id_post_id ON blogs_posts(blog_id, post_id);"
        )

        # comments indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_comments_parent_comment_id ON comments(parent_comment_id);")

    @with_cursor
    def create_user(self, cur: cursor, user_data: dict[str, str]):
        password: str = user_data.pop("password")
        encoded_password: bytes = password.encode("utf-8")
        hashed_password: bytes = bcrypt.hashpw(encoded_password, bcrypt.gensalt())
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO users (username, first_name, last_name, password) VALUES (%s, %s, %s, %s)
            """,
            tuple(user_data.values()) + (hashed_password.decode("utf-8"),),
        )

    @with_cursor
    def autorize_user(self, cur: cursor, credentials: dict[str, str]):
        username = credentials["username"]
        cur.execute("""SELECT username, password FROM users WHERE username = %s;""", (username,))
        user: cursor = cur.fetchone()

        if user is not None:
            if not self._check_password(self, credentials["password"], user[1]):
                raise ValueError(f"Password validation {user[0]} failed!")
        else:
            raise KeyError(f"User '{credentials['username']}' not found!")

        cur.execute(
            """
            UPDATE users
            SET is_authorized = True
            WHERE username = %s
            """,
            (username,),
        )

    @with_cursor
    def users_list(self, cur: cursor):
        cur.execute("""SELECT id, username, first_name, last_name FROM users""")
        return [{"username": item[0], "first_name": item[1], "last_name": item[2]} for item in cur.fetchall()]

    @with_cursor
    def create_blog(self, cur: cursor, blog_data: dict[str, str | int]):
        cur.execute(
            """
            INSERT INTO blogs (title, user_id)
            VALUES (%s, %s)
            """,
            (blog_data["title"], blog_data["user_id"]),
        )

    @with_cursor
    def update_blog(self, cur: cursor, blog_data: dict[str, int]):
        user_id: int = blog_data["user_id"]
        blog_id: int = blog_data["id"]

        cur.execute("""SELECT title FROM blogs WHERE user_id = %s AND id = %s""", (user_id, blog_id))
        author = cur.fetchone()
        if author:
            cur.execute(
                """UPDATE blogs SET title = %s WHERE user_id = %s AND id = %s""",
                (blog_data["title"], user_id, blog_id),
            )
        else:
            raise KeyError(f"Blog '{blog_id}' by author '{user_id}' not found!")

    @with_cursor
    def delete_blog(self, cur: cursor, blog_data: dict[str, int]):
        user_id: int = blog_data["user_id"]
        blog_id: int = blog_data["id"]

        cur.execute("""SELECT title FROM blogs WHERE user_id = %s AND id = %s""", (user_id, blog_id))
        author = cur.fetchone()
        if author:
            cur.execute("""UPDATE blogs SET is_deleted = True WHERE user_id = %s AND id = %s""", ((user_id, blog_id)))
        else:
            raise KeyError(f"Blog '{blog_id}' by author '{user_id}' not found!")

    @with_cursor
    def blogs_list(self, cur: cursor, undeleted_only: bool = False):
        query = """SELECT * FROM blogs"""
        if undeleted_only:
            query += " WHERE is_deleted = False"

        cur.execute(query)
        return [{"id": item[0], "title": item[1], "user_id": item[2], "is_deleted": item[3]} for item in cur.fetchall()]

    @with_cursor
    def undeleted_blogs_list_by_authorized_user(
        self,
        cur: cursor,
    ):
        query = """
            SELECT b.title, b.is_deleted, u.username, u.first_name, u.last_name, u.is_authorized 
            FROM blogs AS b 
            JOIN users AS u ON b.user_id = u.id 
            WHERE u.is_authorized AND NOT b.is_deleted;
        """
        cur.execute(query)
        return [
            {
                "blog_title": item[0],
                "blog_is_deleted": item[1],
                "username": item[2],
                "user_first_name": item[3],
                "user_last_name": item[4],
                "user_is_authorized": item[5],
            }
            for item in cur.fetchall()
        ]

    @with_cursor
    def create_post(self, cur: cursor, post_data: dict[str, int | list[int]]):
        blogs: list[int] = post_data.pop("blogs")  # ty:ignore[invalid-assignment]
        create_post_query = """INSERT INTO posts (title, text) VALUES (%s, %s) RETURNING id;"""
        cur.execute(create_post_query, (post_data["title"], post_data["text"]))
        new_post_id = cur.fetchone()[0]

        link_post_with_blogs_query = """INSERT INTO blogs_posts (post_id, blog_id) VALUES (%s, %s); """

        cur.executemany(link_post_with_blogs_query, [(new_post_id, blog_id) for blog_id in blogs])

    @with_cursor
    def update_post(self, cur: cursor, post_data: dict[str, int | list[int]]):
        post_id = post_data.pop("id")
        new_blogs = set(post_data.pop("blogs", []))  # ty:ignore[invalid-argument-type]

        cur.execute(
            """UPDATE posts SET title = %s, text = %s WHERE id = %s RETURNING id""",
            (post_data.get("title"), post_data.get("text"), post_id),
        )

        cur.execute("""SELECT blog_id FROM blogs_posts WHERE post_id = %s""", (post_id,))

        old_blogs = {item[0] for item in cur.fetchall()}
        to_add = new_blogs - old_blogs
        to_remove = old_blogs - new_blogs

        cur.execute(
            """DELETE FROM blogs_posts WHERE post_id = %s AND blog_id IN %s""",
            (post_id, tuple(to_remove) if to_remove else (0,)),
        )
        cur.executemany(
            """INSERT INTO blogs_posts (post_id, blog_id) VALUES (%s, %s)""", [(post_id, blog_id) for blog_id in to_add]
        )

    @with_cursor
    def delete_post(self, cur: cursor, post_data: dict[str, int]):
        user_id: int = post_data["user_id"]
        post_id: int = post_data["post_id"]

        query = """
            DELETE FROM posts 
            WHERE id IN (
                SELECT p.id
                FROM posts AS p 
                JOIN blogs_posts AS bp ON p.id = bp.post_id 
                JOIN blogs AS b ON b.id = bp.blog_id 
                WHERE b.user_id = %s AND p.id = %s
                )
            RETURNING id;
        """

        cur.execute(query, (user_id, post_id))

        deleted = cur.fetchone()

        if not deleted:
            raise KeyError(f"Post '{post_id}' by author '{user_id}' not found!")

    @with_cursor
    def create_comment(self, cur: cursor, comment_data: dict[str, int]):
        user_id: int = comment_data["user_id"]
        post_id: int = comment_data["post_id"]

        query = """
            INSERT INTO comments (text, user_id, post_id, parent_comment_id)
            VALUES (%s, %s, %s, %s) 
            RETURNING id;
        """
        cur.execute(query, (comment_data["text"], user_id, post_id, comment_data.get("parent_comment_id", None)))
        return cur.fetchone()[0]

    @with_cursor
    def get_comments(self, cur: cursor, comments_data: dict[str, int]):
        query = (
            """SELECT text, user_id, post_id, parent_comment_id FROM comments WHERE post_id = %s AND user_id = %s;"""
        )

        cur.execute(query, (comments_data["post_id"], comments_data["user_id"]))

        return [
            {
                "text": item[0],
                "user_id": item[1],
                "post_id": item[2],
                "parent_comment_id": item[3],
            }
            for item in cur.fetchall()
        ]

    @with_cursor
    def get_comments_tree(self, cur: cursor, root_comment_id: int):
        query = """
            WITH RECURSIVE comment_tree AS (
                SELECT id, text, user_id, post_id, parent_comment_id
                FROM comments
                UNION
                
                SELECT c.id, c.text, c.user_id, c.post_id, c.parent_comment_id
                FROM comments c
                JOIN comment_tree ct ON ct.id = c.parent_comment_id
                )
            SELECT * FROM comment_tree;
        """
        cur.execute(query, (root_comment_id,))
        return [
            {"id": item[0], "text": item[1], "user_id": item[2], "post_id": item[3], "parent_comment_id": item[4]}
            for item in cur.fetchall()
        ]

    @with_cursor
    def get_blog_comments_tree_by_users(self, cur: cursor, blog_id: int, users_filter: tuple[int]):
        query = """
            WITH RECURSIVE comment_tree AS (
                SELECT c.id, c.text, c.user_id, c.post_id, c.parent_comment_id
                FROM comments c
                JOIN posts p ON c.post_id = p.id
                JOIN blogs_posts bp ON p.id = bp.post_id
                WHERE bp.blog_id = %s AND user_id IN %s
                UNION ALL
                
                SELECT c.id, c.text, c.user_id, c.post_id, c.parent_comment_id
                FROM comments c
                
                JOIN comment_tree ct ON ct.id = c.parent_comment_id
                )
            SELECT * FROM comment_tree;
        """
        cur.execute(query, (blog_id, users_filter))
        return [
            {"id": item[0], "text": item[1], "user_id": item[2], "post_id": item[3], "parent_comment_id": item[4]}
            for item in cur.fetchall()
        ]

    @with_cursor
    def generate_dummy_data(self, cur: cursor):
        for i in range(1, 1001):
            self.create_user({
                "username": f"username_{i}",
                "first_name": f"First_Name_{i}",
                "last_name": f"Last_Name_{i}",
                "password": "admin",
            })

        for i in range(1, 101):
            self.create_blog({
                "title": f"blog_{i}",
                "user_id": random.randint(1, 1000),
            })

        for i in range(1, 10001):
            self.create_post({
                "title": f"post_{i}",
                "text": f"random_text_{i}",
                "blogs": [random.randint(1, 100)],
            })

        for i in range(1, 100001):
            self.create_comment({
                "text": f"comment_text_{i}",
                "user_id": random.randint(1, 1000),
                "post_id": random.randint(1, 10000),
                "parent_comment_id": random.randint(1, i) if i > 1 else None,
            })
