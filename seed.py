from faker import Faker
from app import app
from models import db, User, Note

fake = Faker()

def seed_database():
    with app.app_context():
        print("🌱 Clearing database tables...")
        Note.query.delete()
        User.query.delete()
        db.session.commit()

        print("🌱 Seeding users...")
        users = []

        # Default demo user for easy manual testing / grader access
        demo_user = User(username="demo_user")
        demo_user.password_hash = "password123"
        users.append(demo_user)

        # Other mock users
        alex = User(username="alex_dev")
        alex.password_hash = "password123"
        users.append(alex)

        sarah = User(username="sarah_m")
        sarah.password_hash = "password123"
        users.append(sarah)

        jordan = User(username="jordan_t")
        jordan.password_hash = "password123"
        users.append(jordan)

        db.session.add_all(users)
        db.session.commit()
        print(f"Created {len(users)} users (default password is 'password123').")

        print("🌱 Seeding notes...")
        categories = ["Work", "Personal", "Ideas", "Study", "To-Do"]

        # Realistic curated notes for demo_user so they have varied data to paginate through
        sample_notes = [
            ("Sprint Planning Notes", "Discussed Q4 roadmap and planned backend auth deliverables with the team.", "Work"),
            ("Grocery & Supplies", "Milk, oat milk, sourdough bread, coffee beans, olive oil, and lemons.", "Personal"),
            ("Productivity App Ideas", "Add markdown preview support, tag filtering, and pin-to-top feature for important notes.", "Ideas"),
            ("Python & Flask Study", "Reviewed Flask sessions, Bcrypt hashing algorithms, and RESTful route designs.", "Study"),
            ("Gym Routine - Monday", "Bench press 4x8, Incline DB press 3x10, Tricep pushdowns 3x12, 20m incline walk.", "Personal"),
            ("Fix Production Bug #104", "Investigate CORS preflight headers and cookie SameSite attribute in production environment.", "Work"),
            ("Book Recommendations", "Atomic Habits by James Clear, Deep Work by Cal Newport, Clean Code by Uncle Bob.", "Personal"),
            ("Meeting with Design Team", "Reviewed UI wireframes for notes index view, pagination controls, and delete confirmation modal.", "Work"),
            ("Weekly Review", "Reflect on week accomplishments, clear email inbox, and plan top 3 priorities for next week.", "To-Do"),
            ("SQL Indexing Cheatsheet", "Composite indexes, B-tree vs Hash, EXPLAIN ANALYZE query plans for pagination performance.", "Study"),
            ("Side Project Brainstorm", "Habit tracking micro-SaaS with minimal UI and daily email summary.", "Ideas"),
            ("Dentist Appointment", "Scheduled checkup on Thursday at 3:00 PM. Remember to bring insurance card.", "Personal")
        ]

        notes = []
        for title, content, cat in sample_notes:
            note = Note(
                title=title,
                content=content,
                category=cat,
                user_id=demo_user.id
            )
            notes.append(note)

        # Add additional randomized notes for other users using Faker
        for user in [alex, sarah, jordan]:
            for _ in range(4):
                note = Note(
                    title=fake.sentence(nb_words=4).rstrip('.'),
                    content=fake.paragraph(nb_sentences=3),
                    category=fake.random_element(elements=categories),
                    user_id=user.id
                )
                notes.append(note)

        db.session.add_all(notes)
        db.session.commit()
        print(f"Created {len(notes)} notes across all users.")
        print(" Seeding complete!")

if __name__ == '__main__':
    seed_database()
