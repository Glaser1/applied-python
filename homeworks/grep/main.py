def grep(lines, params):
    match = lambda line: params.pattern in line

    if params.ignore_case:
        match = lambda line: params.pattern.lower() in line.lower()

    if params.invert:
        match = lambda line: params.pattern not in line

    if params.count:
        cnt = sum(1 for line in lines if match(line))
        output(str(cnt))

    elif params.context:
        already_added = set()
        match = lambda line: params.pattern in line

        for idx, line in enumerate(lines, start=1):
            if params.line_number:
                line = f"{idx}:{line}"
            if match(line):
                left_limit = min(idx, params.context)
                for line in lines[idx - left_limit : idx]:
                    if line not in already_added:
                        output(line)
                        already_added.add(line)

            output(line)

            right_limit = min(params.context, len(lines) - 1 - idx)
            for line in lines[idx + 1 : idx + right_limit + 1]:
                if line not in already_added:
                    output(line)
                    already_added.add(line)

    else:
        for idx, line in enumerate(lines, start=1):
            if params.line_number:
                line = f"{idx}:{line}"

            if match(line):
                output(line)
