from conftest import PASSWORD, appointments_for, new_client, register, slot, unique_email


def book(c, doctor_id, starts_at, reason="Checkup"):
    return c.post(
        "/appointments", data={"doctor_id": doctor_id, "starts_at": starts_at, "reason": reason}
    )


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_register_login_logout(client):
    email, r = register(client)
    assert r.status_code == 200
    assert "Your appointments" in r.text

    client.post("/logout")
    assert client.get("/appointments", follow_redirects=False).status_code == 303

    bad = client.post("/login", data={"email": email, "password": "wrong-password"})
    assert bad.status_code == 400
    assert "Invalid email or password" in bad.text

    ok = client.post("/login", data={"email": email, "password": PASSWORD})
    assert "Your appointments" in ok.text


def test_register_validation(client):
    _, short = register(client, password="short")
    assert short.status_code == 400

    email, _ = register(client)
    client.post("/logout")
    _, dup = register(client, email=email)
    assert dup.status_code == 400
    assert "already exists" in dup.text


def test_pages_require_login(client):
    for path in ("/appointments", "/appointments/new", "/messages"):
        r = client.get(path, follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"] == "/login"


def test_login_returns_to_requested_page(client):
    email, _ = register(client)
    client.post("/logout")
    client.get("/messages")  # remembers where we were headed
    r = client.post("/login", data={"email": email, "password": PASSWORD})
    assert "<h1>Messages</h1>" in r.text


def test_doctor_search_and_filter(client):
    assert "Cardiology" in client.get("/doctors?q=cardio").text
    filtered = client.get("/doctors?specialty=Dermatology").text
    assert "Dermatology" in filtered
    assert "Dr. Priya Nair" not in filtered
    assert "No doctors match" in client.get("/doctors?q=zzzz-no-match").text
    # LIKE wildcards in the query are treated literally
    assert "No doctors match" in client.get("/doctors?q=%25").text


def test_book_reschedule_cancel(client):
    email, _ = register(client)
    r = book(client, 1, slot(7))
    assert "Appointment booked" in r.text
    appt = appointments_for(email)[0]
    assert appt.status == "scheduled"

    r = client.post(f"/appointments/{appt.id}/reschedule", data={"starts_at": slot(14, 11, 30)})
    assert "Appointment rescheduled" in r.text
    assert appointments_for(email)[0].starts_at.strftime("%H:%M") == "11:30"

    r = client.post(f"/appointments/{appt.id}/cancel")
    assert "Appointment cancelled" in r.text
    assert appointments_for(email)[0].status == "cancelled"


def test_booking_rules(client):
    register(client)
    base = {"doctor_id": 1, "reason": "Checkup"}

    past = client.post("/appointments", data={**base, "starts_at": "2020-01-06T10:00"})
    assert past.status_code == 400 and "future" in past.text

    saturday = "2030-01-05T10:00"
    weekend = client.post("/appointments", data={**base, "starts_at": saturday})
    assert weekend.status_code == 400 and "Monday through Friday" in weekend.text

    off_grid = client.post("/appointments", data={**base, "starts_at": slot(7, 10, 15)})
    assert off_grid.status_code == 400

    no_reason = book(client, 1, slot(7), reason=" ")
    assert no_reason.status_code == 400


def test_double_booking_blocked(client):
    register(client)
    when = slot(7)
    assert book(client, 1, when).status_code == 200

    # same patient, different doctor, same time
    mine = book(client, 2, when)
    assert mine.status_code == 400 and "already have another appointment" in mine.text

    # a different patient, same doctor, same time
    other = new_client()
    register(other)
    taken = book(other, 1, when)
    assert taken.status_code == 400 and "already booked" in taken.text


def test_cancelled_slot_can_be_rebooked(client):
    email, _ = register(client)
    when = slot(7)
    book(client, 1, when)
    client.post(f"/appointments/{appointments_for(email)[0].id}/cancel")
    again = book(client, 1, when)
    assert again.status_code == 200 and "Appointment booked" in again.text


def test_users_cannot_touch_each_others_appointments(client):
    email, _ = register(client)
    book(client, 1, slot(7), reason="Private")
    appt_id = appointments_for(email)[0].id

    intruder = new_client()
    register(intruder)
    assert intruder.post(f"/appointments/{appt_id}/cancel").status_code == 404
    assert intruder.post(f"/appointments/{appt_id}/notes", data={"notes": "x"}).status_code == 404
    assert "Private" not in intruder.get("/appointments").text
    assert appointments_for(email)[0].status == "scheduled"


def test_visit_notes(client):
    email, _ = register(client)
    book(client, 1, slot(7))
    appt_id = appointments_for(email)[0].id
    r = client.post(f"/appointments/{appt_id}/notes", data={"notes": "Ask about vitamin D"})
    assert "Notes saved" in r.text and "Ask about vitamin D" in r.text


def test_messaging(client):
    register(client)
    r = client.post("/messages/1", data={"body": "Is fasting required before my visit?"})
    assert "Is fasting required" in r.text
    assert "Automated reply" in r.text

    client.post("/messages/1", data={"body": "Second question"})
    thread = client.get("/messages/1").text
    assert thread.count("Automated reply") == 1  # only the first message gets an auto-reply

    empty = client.post("/messages/1", data={"body": "   "})
    assert "Write a message" in empty.text

    inbox = client.get("/messages").text
    assert "Dr. Maya Okafor" in inbox
    assert client.get("/messages/9999").status_code == 404


def test_message_threads_are_private(client):
    register(client)
    client.post("/messages/1", data={"body": "Confidential question"})

    other = new_client()
    register(other, email=unique_email())
    assert "Confidential question" not in other.get("/messages/1").text
