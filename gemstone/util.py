def compress_config_data(config_data, skip_compression=None):
    # @config_data is list of (addr, value) pairs.
    reg_map = {}
    skipped_config_data = []
    if skip_compression is None:
        skip_compression = set()
    for addr, value in config_data:
        if addr in skip_compression:
            skipped_config_data.append((addr, value))
            continue
        if addr not in reg_map:
            reg_map[addr] = 0
        # Assume it's already shifted upstream (e.g. by get_config_data).
        reg_map[addr] = reg_map[addr] | value
    result = []
    for addr, value in reg_map.items():
        if value != 0:
            result.append((addr, value))
    result = result + skipped_config_data
    return result
