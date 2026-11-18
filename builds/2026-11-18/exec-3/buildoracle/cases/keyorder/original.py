def summarize(person):
    name, years_alive = person
    age = years_alive * 1.0
    return {"name": name, "age": age, "active": True}
