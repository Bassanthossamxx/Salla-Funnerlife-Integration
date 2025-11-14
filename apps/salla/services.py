def extract_player_id(item):
    opts = item.get("options", [])
    if len(opts) < 1:
        raise Exception("Missing Player ID option")

    values = opts[0].get("value", [])
    if not values:
        raise Exception("Player ID option has no value")

    return values[0]


def extract_zone_id(item):
    opts = item.get("options", [])
    if len(opts) < 2:
        return None  # No zone ID → not Mobile Legends

    values = opts[1].get("value", [])
    return values[0] if values else None

def build_target(player_id, zone_id, funner_service):
    category = funner_service.get("category")

    # Only ML has zone ID entered by the customer
    if category == "Mobile Legends" and zone_id:
        return f"{player_id}|{zone_id}"

    return player_id

