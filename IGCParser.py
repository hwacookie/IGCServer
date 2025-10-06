import datetime

def parse(filepath: str) -> dict:
    """
    Parses an IGC file to extract header information and flight times.
    Handles variations from different logger manufacturers (e.g., XCTrack, SkyTraxx).
    """
    headers = {}
    start_time = None
    end_time = None
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith('H'):
                    # XCTrack format: HFPLTPILOTINCHARGE:Some Pilot
                    if line.startswith('HFPLTPILOTINCHARGE:'):
                        headers['pilot'] = line.split(':', 1)[1].strip()
                    # SkyTraxx format: HFPLTPILOT:Some Pilot
                    elif line.startswith('HFPLTPILOT:'):
                        headers['pilot'] = line.split(':', 1)[1].strip()
                    elif line.startswith('HFFXA'):
                        pass
                    # XCTrack format: HFDTEDATE:DDMMYY,someotherstuff
                    elif line.startswith('HFDTEDATE:'):
                        date_str = line.split(':', 1)[1].split(',')[0].strip()
                        try:
                            date_obj = datetime.datetime.strptime(date_str, '%d%m%y')
                            headers['date'] = date_obj.strftime('%Y-%m-%d')
                        except ValueError:
                            headers['date'] = ''
                    # SkyTraxx format: HFDTE<DDMMYY>
                    elif line.startswith('HFDTE'):
                        date_str = line[5:].strip()
                        try:
                            date_obj = datetime.datetime.strptime(date_str, '%d%m%y')
                            headers['date'] = date_obj.strftime('%Y-%m-%d')
                        except ValueError:
                            headers['date'] = ''

                    # XCTrack format: HOSITSite:Some Site
                    elif line.startswith('HOSITSite:'):
                        headers['location'] = line.split(':', 1)[1].strip()
                    # SkyTraxx format: HFSITSITE:Some Site
                    elif line.startswith('HFSITSITE:'):
                        headers['location'] = line.split(':', 1)[1].strip()

                    # Common format: HFGTYGLIDERTYPE:Some Glider
                    elif line.startswith('HFGTYGLIDERTYPE:'):
                        headers['glider_model'] = line.split(':', 1)[1].strip()
                
                elif line.startswith('B'):
                    time_str = line[1:7]
                    if start_time is None:
                        start_time = time_str
                    end_time = time_str

    except Exception:
        return {}

    headers['start_time'] = ''
    headers['duration'] = ''
    if start_time and end_time:
        try:
            st = datetime.datetime.strptime(start_time, '%H%M%S').time()
            et = datetime.datetime.strptime(end_time, '%H%M%S').time()
            duration = datetime.datetime.combine(datetime.date.min, et) - datetime.datetime.combine(datetime.date.min, st)
            headers['start_time'] = st.strftime('%H:%M:%S')
            headers['duration'] = str(duration)
        except ValueError:
            pass

    return headers
