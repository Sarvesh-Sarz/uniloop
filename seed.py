"""
Uniloop Database Seeder

Populates the database with:
- 1 Admin account (admin@university.edu)
- 12 Student accounts across different departments & years
- 24 Realistic campus listings across 7 categories with generated SVG photos
- Active rentals with various countdowns (due in 4 days, due tomorrow, due today)
- Overdue rentals with calculated late fees (overdue by 2 days)
- Completed rentals with peer ratings & reviews
- In-app notifications, peer messages, and saved wishlist items
"""

import os
from datetime import date, datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.listing import Listing, ListingImage
from app.models.rental import RentalRequest, Rental
from app.models.rating import Rating
from app.models.message import Message
from app.models.notification import Notification
from app.models.wishlist import Wishlist
from app.models.report import Report
from app.auth import hash_password
from app.services.rental_service import calculate_rental_quote, calculate_late_fee


# SVG icon generator helper for clean, beautiful placeholder images
def generate_svg_image(filename: str, title: str, category: str, bg_color: str, icon_svg: str) -> str:
    os.makedirs("uploads", exist_ok=True)
    filepath = os.path.join("uploads", filename)
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
  <defs>
    <linearGradient id="grad_{filename[:6]}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg_color}" stop-opacity="0.9" />
      <stop offset="100%" stop-color="{bg_color}" stop-opacity="1" />
    </linearGradient>
  </defs>
  <rect width="600" height="400" rx="16" fill="url(#grad_{filename[:6]})"/>
  <g transform="translate(240, 90)" fill="#ffffff" opacity="0.95">
    {icon_svg}
  </g>
  <text x="300" y="270" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="22" font-weight="700" fill="#ffffff" text-anchor="middle">{title}</text>
  <rect x="230" y="295" width="140" height="28" rx="14" fill="#ffffff" fill-opacity="0.25"/>
  <text x="300" y="314" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13" font-weight="600" fill="#ffffff" text-anchor="middle" letter-spacing="1">{category.upper()}</text>
</svg>"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(svg_content)
    return f"/uploads/{filename}"


# Simple SVG paths for item icons
ICONS = {
    "book": '<path d="M12 60 L108 60 L108 12 C108 12 84 0 60 12 C36 0 12 12 12 12 Z M60 12 L60 60" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>',
    "calc": '<rect x="16" y="8" width="88" height="104" rx="12" fill="none" stroke="#ffffff" stroke-width="8"/><rect x="28" y="20" width="64" height="24" rx="4" fill="#ffffff"/><circle cx="36" cy="60" r="6" fill="#ffffff"/><circle cx="60" cy="60" r="6" fill="#ffffff"/><circle cx="84" cy="60" r="6" fill="#ffffff"/><circle cx="36" cy="80" r="6" fill="#ffffff"/><circle cx="60" cy="80" r="6" fill="#ffffff"/><circle cx="84" cy="80" r="6" fill="#ffffff"/><circle cx="36" cy="100" r="6" fill="#ffffff"/><circle cx="60" cy="100" r="6" fill="#ffffff"/><circle cx="84" cy="100" r="6" fill="#ffffff"/>',
    "chip": '<rect x="24" y="24" width="72" height="72" rx="8" fill="none" stroke="#ffffff" stroke-width="8"/><path d="M40 8 L40 24 M60 8 L60 24 M80 8 L80 24 M40 96 L40 112 M60 96 L60 112 M80 96 L80 112 M8 40 L24 40 M8 60 L24 60 M8 80 L24 80 M96 40 L112 40 M96 60 L112 60 M96 80 L112 80" stroke="#ffffff" stroke-width="6" stroke-linecap="round"/>',
    "lab": '<path d="M44 16 L76 16 M60 16 L60 44 L96 96 C102 106 94 116 82 116 L38 116 C26 116 18 106 24 96 L60 44" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/><circle cx="50" cy="95" r="4" fill="#ffffff"/><circle cx="68" cy="85" r="5" fill="#ffffff"/>',
    "coat": '<path d="M30 16 L60 36 L90 16 L108 40 L84 56 L84 116 L36 116 L36 56 L12 40 Z M60 36 L60 116" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/><circle cx="52" cy="65" r="3" fill="#ffffff"/><circle cx="52" cy="85" r="3" fill="#ffffff"/>',
    "tool": '<path d="M76 20 C68 12 56 12 48 20 L20 48 C12 56 12 68 20 76 L28 84 L12 100 L20 108 L36 92 L44 100 C52 108 64 108 72 100 L100 72 C108 64 108 52 100 44 Z" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>',
    "draw": '<rect x="16" y="16" width="88" height="88" rx="8" fill="none" stroke="#ffffff" stroke-width="8"/><path d="M16 80 L60 36 L104 80 M16 48 L48 16" stroke="#ffffff" stroke-width="6" stroke-linecap="round"/>'
}


def seed():
    # Recreate tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    print("Populating Uniloop database with realistic demo data...")

    # 1. Create Admin Account
    admin_pw = hash_password("AdminPassword123!")
    admin_user = User(
        name="Campus Admin",
        email="admin@university.edu",
        password_hash=admin_pw,
        department="Academic Affairs",
        year="Staff / Admin",
        role="admin",
        trust_score=100,
        average_rating=5.0,
        rating_count=10,
        is_active=True
    )
    db.add(admin_user)
    db.flush()

    # 2. Create 12 Students with varying trust scores
    student_pw = hash_password("Password123!")
    students_data = [
        ("Sarah Chen", "sarah@university.edu", "Computer Science", "3rd Year", 94, 4.9, 14),
        ("Alex Rivera", "alex@university.edu", "Mechanical", "2nd Year", 88, 4.8, 9),
        ("Priya Sharma", "priya@university.edu", "Electronics", "4th Year", 92, 5.0, 18),
        ("David Kim", "david@university.edu", "Electrical", "1st Year", 55, 4.5, 2),
        ("Maya Patel", "maya@university.edu", "Civil", "3rd Year", 78, 4.7, 8),
        ("Marcus Brody", "marcus@university.edu", "Computer Science", "Postgraduate", 96, 4.95, 22),
        ("Ananya Roy", "ananya@university.edu", "Information Technology", "2nd Year", 62, 4.6, 5),
        ("Ethan Walker", "ethan@university.edu", "Mechanical", "3rd Year", 81, 4.7, 11),
        ("Rohan Verma", "rohan@university.edu", "Electronics", "2nd Year", 70, 4.5, 6),
        ("Chloe Bennett", "chloe@university.edu", "Chemical", "4th Year", 85, 4.85, 12),
        ("Liam O'Connor", "liam@university.edu", "Physics / Science", "1st Year", 50, 5.0, 1),
        ("Aisha Khan", "aisha@university.edu", "Computer Science", "3rd Year", 89, 4.9, 15),
    ]

    students = []
    for name, email, dept, yr, trust, avg_r, r_cnt in students_data:
        s = User(
            name=name,
            email=email,
            password_hash=student_pw,
            department=dept,
            year=yr,
            role="student",
            trust_score=trust,
            average_rating=avg_r,
            rating_count=r_cnt,
            is_active=True
        )
        db.add(s)
        students.append(s)

    db.flush()

    # 3. Create 24 Listings across 7 Categories
    # We assign owners in a round-robin or realistic distribution
    listings_meta = [
        # (title, category, condition, type, day, week, deposit, max_d, loc, is_semester, desc, owner_idx, icon, color)
        ("Introduction to Algorithms (CLRS 4th Ed)", "Textbooks", "Like New", "paid", 35.0, 180.0, 400.0, 60, "Main Library", True, "Essential reference for CS algorithms and data structures. Pristine condition with no markings or highlights.", 0, "book", "#2563eb"),
        ("Casio FX-991EX ClassWiz Scientific Calculator", "Calculators", "Good", "paid", 20.0, 100.0, 250.0, 30, "Engineering Block", True, "High-resolution display with matrix, equation solver, and spreadsheet functions. Batteries freshly replaced.", 1, "calc", "#4f46e5"),
        ("Digital Storage Oscilloscope 50MHz (Hantek)", "Lab Equipment", "Good", "paid", 95.0, 500.0, 1200.0, 14, "Science Block", False, "Dual-channel 50MHz digital oscilloscope with probes, USB cable, and calibration certificate. Great for embedded projects.", 2, "chip", "#0891b2"),
        ("Arduino Mega 2560 Ultimate Starter Kit", "Electronics", "Like New", "paid", 40.0, 200.0, 450.0, 21, "Hostel Block A", True, "Complete kit with 60+ sensors, LCD screen, stepper motors, jumper wires, and breadboards.", 0, "chip", "#059669"),
        ("Unisex White Laboratory Coat (Size M)", "Lab Coats", "Good", "free", 0.0, 0.0, 100.0, 14, "Cafeteria", True, "100% thick cotton lab coat meeting campus lab safety standards. Cleaned and pressed.", 9, "coat", "#d97706"),
        ("Precision Electronics Repair Screwdriver Kit 64-in-1", "Tools", "New", "paid", 25.0, 120.0, 200.0, 14, "Student Center", False, "Magnetic screwdriver set with flexible extension, tweezers, and opening picks for laptops and smartphones.", 4, "tool", "#dc2626"),
        ("Calculus: Early Transcendentals (Stewart 8th Ed)", "Textbooks", "Good", "paid", 30.0, 150.0, 350.0, 90, "Main Library", True, "Standard textbook for MAT101 and MAT102. Contains all chapters on multi-variable calculus.", 5, "book", "#7c3aed"),
        ("Texas Instruments TI-84 Plus CE Color Graphing Calc", "Calculators", "Like New", "paid", 45.0, 220.0, 600.0, 30, "Hostel Block B", False, "Rechargeable color screen graphing calculator, preloaded with polynomial root finder and conic apps.", 2, "calc", "#db2777"),
        ("Raspberry Pi 4 Model B (4GB) with Official Case", "Electronics", "Like New", "paid", 50.0, 250.0, 700.0, 21, "Engineering Block", True, "Quad-core 1.5GHz, 4GB RAM, dual micro-HDMI 4K, 32GB MicroSD with Raspberry Pi OS pre-installed.", 3, "chip", "#16a34a"),
        ("Engineering Drawing Board with T-Square & Clips", "Tools", "Good", "free", 0.0, 0.0, 150.0, 45, "Engineering Block", True, "A2 size drafting board with parallel motion ruler, protractor, and set squares. Perfect for 1st/2nd year CAD & drawing.", 1, "draw", "#ca8a04"),
        ("Microelectronic Circuits by Sedra & Smith (7th Ed)", "Textbooks", "Used", "free", 0.0, 0.0, 200.0, 60, "Science Block", False, "Classic textbook for Analog & Digital circuits. Well loved, slightly worn cover, but all pages intact.", 8, "book", "#2563eb"),
        ("Digital Multimeter with Auto-Ranging & Temp Probe", "Lab Equipment", "Like New", "paid", 30.0, 150.0, 300.0, 14, "Hostel Block A", False, "Measures AC/DC voltage, current, resistance, capacitance, and continuity buzzer. Backlit LCD.", 7, "chip", "#0d9488"),
        ("Operating System Concepts ('Dinosaur Book' 10th Ed)", "Textbooks", "Like New", "paid", 35.0, 180.0, 400.0, 60, "Main Library", True, "Complete guide to OS kernels, memory management, threads, and file systems. Clean copy.", 11, "book", "#4338ca"),
        ("Soldering Station 60W with Temperature Control", "Tools", "Good", "paid", 35.0, 175.0, 350.0, 10, "Engineering Block", False, "Ceramic heater with adjustable 200°C-480°C dial, brass tip cleaner, solder wire, and heat-resistant stand.", 6, "tool", "#ea580c"),
        ("Biological Compound Microscope (1000x Magnification)", "Lab Equipment", "Like New", "paid", 80.0, 420.0, 1000.0, 7, "Science Block", False, "Monocular head with 10x and 25x eyepieces, LED illumination, and slide preparation kit.", 9, "lab", "#0284c7"),
        ("White Lab Coat with Splash Goggles (Size L)", "Lab Coats", "New", "paid", 15.0, 70.0, 150.0, 14, "Cafeteria", False, "Never used lab coat with anti-fog safety goggles. Required for Chemistry & Biotech practical exams.", 10, "coat", "#b45309"),
        ("FPGA Development Board (Altera Cyclone IV)", "Electronics", "Like New", "paid", 75.0, 380.0, 900.0, 21, "Engineering Block", False, "Includes 8-digit 7-segment display, push buttons, VGA port, and USB-Blaster programmer for Verilog/VHDL.", 2, "chip", "#6d28d9"),
        ("Vernier Caliper 150mm Stainless Steel", "Tools", "Like New", "free", 0.0, 0.0, 100.0, 14, "Student Center", False, "High accuracy 0.02mm resolution with internal, external, depth, and step measuring faces.", 4, "tool", "#475569"),
        ("Fluid Mechanics Fundamentals & Applications (Cengel)", "Textbooks", "Good", "paid", 30.0, 150.0, 350.0, 45, "Main Library", False, "Comprehensive textbook covering fluid statics, Bernoulli equation, pipe flow, and turbomachinery.", 1, "book", "#1d4ed8"),
        ("Organic Chemistry (Wade 9th Ed) with Model Kit", "Textbooks", "Like New", "paid", 40.0, 200.0, 450.0, 60, "Science Block", True, "Includes the hardcover textbook plus a 240-piece organic molecular structure building kit for exams.", 9, "book", "#9333ea"),
        ("USB Logic Analyzer 8-Channel 24MHz", "Electronics", "Like New", "paid", 25.0, 120.0, 250.0, 14, "Hostel Block B", False, "Compatible with PulseView and Saleae software. Decodes I2C, SPI, UART, and CAN bus protocols.", 0, "chip", "#059669"),
        ("Scientific Calculator Casio FX-82MS (2nd Ed)", "Calculators", "Good", "free", 0.0, 0.0, 100.0, 30, "Cafeteria", False, "Two-line display scientific calculator for general mathematics and physics courses.", 7, "calc", "#3b82f6"),
        ("Sony Noise Cancelling Over-Ear Headphones", "Other", "Like New", "paid", 60.0, 320.0, 800.0, 14, "Main Library", True, "Active noise cancelling headphones for deep study sessions in noisy dorms. 30h battery life.", 5, "chip", "#0f172a"),
        ("Metric Socket Wrench Set 46-Piece in Hard Case", "Tools", "Good", "paid", 35.0, 180.0, 350.0, 7, "Hostel Block A", False, "1/4 inch drive ratchet handle, extension bars, and torx/hex/slotted sockets for mechanics projects.", 7, "tool", "#334155"),
    ]

    listings = []
    for idx, item in enumerate(listings_meta):
        title, cat, cond, rtype, p_day, p_wk, dep, max_d, loc, is_sem, desc, o_idx, icon_key, color = item
        owner = students[o_idx]

        # Generate SVG image for this listing
        img_filename = f"item_{idx + 1}_{cat.lower().replace(' ', '_')}.svg"
        img_url = generate_svg_image(
            filename=img_filename,
            title=title[:28] + ("..." if len(title) > 28 else ""),
            category=cat,
            bg_color=color,
            icon_svg=ICONS.get(icon_key, ICONS["book"])
        )

        listing = Listing(
            owner_id=owner.id,
            title=title,
            description=desc,
            category=cat,
            condition=cond,
            rental_type=rtype,
            price_per_day=p_day,
            price_per_week=p_wk,
            security_deposit=dep,
            max_duration_days=max_d,
            pickup_location=loc,
            status="available",
            is_semester_resource=is_sem
        )
        db.add(listing)
        db.flush()

        img = ListingImage(listing_id=listing.id, image_url=img_url, is_primary=True)
        db.add(img)
        listings.append(listing)

    db.flush()

    # 4. Create Active Rentals with Live Countdowns
    today = date.today()

    # Rental 1: Due in 4 days (Sarah Chen -> Alex Rivera)
    # Listing: Algorithms Book (listings[0])
    listings[0].status = "rented"
    quote1 = calculate_rental_quote(listings[0].price_per_day, listings[0].price_per_week, listings[0].security_deposit, listings[0].rental_type, today - timedelta(days=3), today + timedelta(days=4))
    r1 = Rental(
        listing_id=listings[0].id,
        owner_id=listings[0].owner_id,
        borrower_id=students[1].id,  # Alex Rivera
        start_date=today - timedelta(days=3),
        end_date=today + timedelta(days=4),
        rental_cost=quote1["rental_cost"],
        security_deposit=quote1["security_deposit"],
        late_fee=0.0,
        deposit_status="HELD",
        status="ACTIVE"
    )
    db.add(r1)

    # Rental 2: Due tomorrow (Priya Sharma -> David Kim)
    # Listing: TI-84 Plus CE (listings[7])
    listings[7].status = "rented"
    quote2 = calculate_rental_quote(listings[7].price_per_day, listings[7].price_per_week, listings[7].security_deposit, listings[7].rental_type, today - timedelta(days=6), today + timedelta(days=1))
    r2 = Rental(
        listing_id=listings[7].id,
        owner_id=listings[7].owner_id,
        borrower_id=students[3].id,  # David Kim
        start_date=today - timedelta(days=6),
        end_date=today + timedelta(days=1),
        rental_cost=quote2["rental_cost"],
        security_deposit=quote2["security_deposit"],
        late_fee=0.0,
        deposit_status="HELD",
        status="ACTIVE"
    )
    db.add(r2)

    # Rental 3: Due today (Alex Rivera -> Maya Patel)
    # Listing: Casio FX-991EX (listings[1])
    listings[1].status = "rented"
    quote3 = calculate_rental_quote(listings[1].price_per_day, listings[1].price_per_week, listings[1].security_deposit, listings[1].rental_type, today - timedelta(days=5), today)
    r3 = Rental(
        listing_id=listings[1].id,
        owner_id=listings[1].owner_id,
        borrower_id=students[4].id,  # Maya Patel
        start_date=today - timedelta(days=5),
        end_date=today,
        rental_cost=quote3["rental_cost"],
        security_deposit=quote3["security_deposit"],
        late_fee=0.0,
        deposit_status="HELD",
        status="ACTIVE"
    )
    db.add(r3)

    # Rental 4: Overdue by 2 days (Marcus Brody -> Liam O'Connor)
    # Listing: Noise Cancelling Headphones (listings[22])
    listings[22].status = "rented"
    quote4 = calculate_rental_quote(listings[22].price_per_day, listings[22].price_per_week, listings[22].security_deposit, listings[22].rental_type, today - timedelta(days=7), today - timedelta(days=2))
    overdue_days, late_fee = calculate_late_fee(today - timedelta(days=2), today, 25.0)
    r4 = Rental(
        listing_id=listings[22].id,
        owner_id=listings[22].owner_id,
        borrower_id=students[10].id,  # Liam O'Connor
        start_date=today - timedelta(days=7),
        end_date=today - timedelta(days=2),
        rental_cost=quote4["rental_cost"],
        security_deposit=quote4["security_deposit"],
        late_fee=late_fee,
        deposit_status="HELD",
        status="OVERDUE"
    )
    db.add(r4)

    # 5. Completed Rentals with Ratings
    # Completed Rental A: Stewart Calculus (Marcus Brody -> Sarah Chen)
    quote_c1 = calculate_rental_quote(listings[6].price_per_day, listings[6].price_per_week, listings[6].security_deposit, listings[6].rental_type, today - timedelta(days=25), today - timedelta(days=10))
    r_comp1 = Rental(
        listing_id=listings[6].id,
        owner_id=listings[6].owner_id,
        borrower_id=students[0].id,  # Sarah
        start_date=today - timedelta(days=25),
        end_date=today - timedelta(days=10),
        actual_return_date=today - timedelta(days=10),
        rental_cost=quote_c1["rental_cost"],
        security_deposit=quote_c1["security_deposit"],
        late_fee=0.0,
        deposit_status="REFUNDED",
        status="COMPLETED"
    )
    db.add(r_comp1)
    db.flush()

    # Reviews for Completed Rental A
    rating1 = Rating(
        rental_id=r_comp1.id,
        reviewer_id=students[0].id,  # Sarah reviews Marcus
        reviewed_user_id=listings[6].owner_id,
        rating=5,
        review="Book was in immaculate condition. Marcus met me right on time at the library. Highly recommended!"
    )
    rating2 = Rating(
        rental_id=r_comp1.id,
        reviewer_id=listings[6].owner_id,  # Marcus reviews Sarah
        reviewed_user_id=students[0].id,
        rating=5,
        review="Sarah returned the book early and in the exact same condition. Excellent campus borrower!"
    )
    db.add_all([rating1, rating2])

    # Completed Rental B: Multimeter (Ethan Walker -> Priya Sharma)
    quote_c2 = calculate_rental_quote(listings[11].price_per_day, listings[11].price_per_week, listings[11].security_deposit, listings[11].rental_type, today - timedelta(days=14), today - timedelta(days=7))
    r_comp2 = Rental(
        listing_id=listings[11].id,
        owner_id=listings[11].owner_id,
        borrower_id=students[2].id,  # Priya
        start_date=today - timedelta(days=14),
        end_date=today - timedelta(days=7),
        actual_return_date=today - timedelta(days=7),
        rental_cost=quote_c2["rental_cost"],
        security_deposit=quote_c2["security_deposit"],
        late_fee=0.0,
        deposit_status="REFUNDED",
        status="COMPLETED"
    )
    db.add(r_comp2)
    db.flush()

    rating3 = Rating(
        rental_id=r_comp2.id,
        reviewer_id=students[2].id,
        reviewed_user_id=listings[11].owner_id,
        rating=5,
        review="Multimeter worked flawlessly for our Senior Design circuit debugging. Ethan even threw in extra crocodile clips!"
    )
    db.add(rating3)

    # 6. Sample Pending Rental Request
    # Alex Rivera requested Sarah Chen's Arduino Kit (listings[3])
    req1 = RentalRequest(
        listing_id=listings[3].id,
        borrower_id=students[1].id,  # Alex
        start_date=today + timedelta(days=1),
        end_date=today + timedelta(days=7),
        message="Hi Sarah! I need your Arduino Mega kit for my microcontrollers lab next week. Can we meet at the Engineering Block?",
        status="REQUESTED"
    )
    db.add(req1)

    # 7. Notifications
    notifs = [
        Notification(
            user_id=students[0].id,
            title="New Rental Request",
            message="Alex Rivera has requested to borrow/rent 'Arduino Mega 2560 Ultimate Starter Kit'.",
            link="/rentals.html?tab=lent",
            is_read=False
        ),
        Notification(
            user_id=students[1].id,
            title="Rental Active",
            message="Your rental for 'Introduction to Algorithms' is active. 4 days remaining.",
            link="/rentals.html?tab=borrowed",
            is_read=True
        ),
        Notification(
            user_id=students[10].id,
            title="Rental Overdue Alert",
            message="Your rental for 'Sony Noise Cancelling Headphones' is overdue by 2 days. A late fee of ₹50 has accrued.",
            link="/rentals.html?tab=overdue",
            is_read=False
        ),
        Notification(
            user_id=students[0].id,
            title="Trust Score Boost",
            message="Your trust score increased by +5 for completing an on-time return! Current score: 94/100.",
            link="/profile.html",
            is_read=False
        ),
    ]
    db.add_all(notifs)

    # 8. Sample Messages
    msgs = [
        Message(
            sender_id=students[1].id,
            receiver_id=students[0].id,
            listing_id=listings[3].id,
            message="Hey Sarah, does the Arduino kit include the ultrasonic distance sensor?",
            is_read=True,
            created_at=datetime.utcnow() - timedelta(hours=3)
        ),
        Message(
            sender_id=students[0].id,
            receiver_id=students[1].id,
            listing_id=listings[3].id,
            message="Yes it does! Both the HC-SR04 ultrasonic sensor and the PIR motion sensor are in the plastic divider box.",
            is_read=False,
            created_at=datetime.utcnow() - timedelta(hours=1)
        ),
    ]
    db.add_all(msgs)

    # 9. Wishlist entries
    wishes = [
        Wishlist(user_id=students[0].id, listing_id=listings[2].id),  # Sarah saved Oscilloscope
        Wishlist(user_id=students[1].id, listing_id=listings[8].id),  # Alex saved Raspberry Pi
        Wishlist(user_id=students[2].id, listing_id=listings[16].id), # Priya saved FPGA board
    ]
    db.add_all(wishes)

    # 10. Sample Reports
    sample_report = Report(
        reporter_id=students[1].id,
        reported_user_id=students[10].id,
        category="Suspicious communication",
        description="User asked to pay outside the platform and avoid meeting on campus. Please review.",
        status="OPEN"
    )
    db.add(sample_report)

    db.commit()
    db.close()
    print("Database seeding completed successfully!")
    print(f"Admin login: admin@university.edu / AdminPassword123!")
    print(f"Student A (Sarah): sarah@university.edu / Password123!")
    print(f"Student B (Alex): alex@university.edu / Password123!")


if __name__ == "__main__":
    seed()
