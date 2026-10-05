from .db import connect


def migrate():
    with connect() as conn:
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(questions)")
        }

        if "question_origin" not in columns:
            conn.execute("""
                ALTER TABLE questions
                ADD COLUMN question_origin TEXT NOT NULL DEFAULT 'reported'
            """)
            print("Added: question_origin")
        else:
            print("Already exists: question_origin")

        if "report_count" not in columns:
            conn.execute("""
                ALTER TABLE questions
                ADD COLUMN report_count INTEGER NOT NULL DEFAULT 1
            """)
            print("Added: report_count")
        else:
            print("Already exists: report_count")

        if "duplicate_of" not in columns:
            conn.execute("""
                ALTER TABLE questions
                ADD COLUMN duplicate_of INTEGER
            """)
            print("Added: duplicate_of")
        else:
            print("Already exists: duplicate_of")
            
        conn.commit()

    print("Migration completed.")


if __name__ == "__main__":
    migrate()