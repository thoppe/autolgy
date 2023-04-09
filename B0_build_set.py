import os

with open("phraselist.txt") as FIN:
    for topic in FIN:
        topic = topic.strip()
        if not topic:
            continue

        cmd = f'python P0_build_ontolog.py --topic "{topic}"'
        os.system(cmd)

        for mode in ["definition", "emoji", "examples"]:
            cmd = f'python P1_gather_defs.py --topic "{topic}" --mode {mode}'
            os.system(cmd)
