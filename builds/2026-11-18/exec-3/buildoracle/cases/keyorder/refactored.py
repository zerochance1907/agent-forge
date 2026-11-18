def summarize(person):
    name, years_alive = person
    age = (years_alive * 3) / 3
    return {"active": True, "age": age, "name": name}
