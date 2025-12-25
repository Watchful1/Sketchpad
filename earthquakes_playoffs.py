

def outcome_to_str(home, away, home_outcome):
	if home_outcome == "win":
		return f"{home} beats {away}"
	elif home_outcome == "loss":
		return f"{away} beats {home}"
	else:
		return f"{home} ties {away}"


def points_to_str(sorted_outcome_points):
	bldr = []
	for team, points in sorted_outcome_points:
		bldr.append(f"{team}: {points}")
	return " | ".join(bldr)

def add_all_outcomes(parent_outcomes, remaining_matches):
	possible_outcomes = []
	if len(remaining_matches):
		for home_outcome in ["win","loss","tie"]:
			home, away = remaining_matches[0]
			inner_outcomes = parent_outcomes.copy()
			inner_outcomes.append((home, away, home_outcome))
			current_outcomes, possible_outcomes_old = add_all_outcomes(inner_outcomes, remaining_matches[1:])
			if len(possible_outcomes_old):
				possible_outcomes.extend(possible_outcomes_old)
			else:
				possible_outcomes.append(current_outcomes)
			#print(current_outcomes)
			if len(parent_outcomes) <= 3:
				print(f"{len(possible_outcomes)}")
			#if len(possible_outcomes) > 0 and len(possible_outcomes) % 1000 == 0:


	# for match_num in range(len(remaining_matches)):
	# 	for home_outcome in ["win","loss","tie"]:
	# 		home, away = remaining_matches[match_num]
	# 		inner_outcomes = parent_outcomes.copy()
	# 		inner_outcomes.append((home, away, home_outcome))
	# 		current_outcomes, possible_outcomes_old = add_all_outcomes(inner_outcomes, remaining_matches[1:])
	# 		if len(possible_outcomes_old):
	# 			possible_outcomes.extend(possible_outcomes_old)
	# 		else:
	# 			possible_outcomes.append(current_outcomes)
	# 		#print(current_outcomes)
	# 		if len(parent_outcomes) <= 3:
	# 			print(f"{len(possible_outcomes)}: {match_num}")
	# 		#if len(possible_outcomes) > 0 and len(possible_outcomes) % 1000 == 0:

		# for home_score in range(0, 5):
		# 	for away_score in range(0, 5):
		# 		home, away = remaining_matches[match_num]
		# 		inner_outcomes = parent_outcomes.copy()
		# 		inner_outcomes.append((home, away, home_score, away_score))
		# 		current_outcomes, possible_outcomes_old = add_all_outcomes(inner_outcomes, remaining_matches[1:])
		# 		if len(possible_outcomes_old):
		# 			possible_outcomes.extend(possible_outcomes_old)
		# 		else:
		# 			possible_outcomes.append(current_outcomes)
		# 		#print(current_outcomes)
		# 		if len(parent_outcomes) <= 3:
		# 			print(f"{len(possible_outcomes)}: {match_num}")
		# 		#if len(possible_outcomes) > 0 and len(possible_outcomes) % 1000 == 0:

	return parent_outcomes, possible_outcomes



if __name__ == "__main__":
	# current_teams = {
	# 	"austin": 44,
	# 	"portland": 44,
	# 	"dallas": 41,
	# 	"colorado": 40,
	# 	"san jose": 38,
	# 	"salt lake": 37,
	# 	#"houston": 36,
	# }
	# pending_matches = [
	# 	("austin", "st louis", "loss", "10-04"),
	# 	("seattle", "portland", "win", "10-04"),
	# 	("salt lake", "colorado", "win", "10-04"),
	# 	("dallas", "galaxy", "win", "10-04"),
	# 	#("houston", "san diego", "loss", "10-04"),
	# 	("vancouver", "san jose", "pending", "10-05"),
	# 	("galaxy", "dallas", "pending", "10-11"),
	# 	("seattle", "salt lake", "pending", "10-11"),
	# 	("austin", "lafc", "pending", "10-12"),
	# 	("portland", "san diego", "pending", "10-18"),
	# 	("colorado", "lafc", "pending", "10-18"),
	# 	("san jose", "austin", "pending", "10-18"),
	# 	("vancouver", "dallas", "pending", "10-18"),
	# 	("st louis", "salt lake", "pending", "10-18"),
	# 	#("kansas", "houston", "pending", "10-18"),
	# ]

	current_teams = {
		"dallas": 38,
		"colorado": 40,
		"san jose": 38,
		"salt lake": 37,
		#"houston": 36,
	}
	pending_matches = [
		("salt lake", "colorado", "win", "10-04"),
		("dallas", "galaxy", "win", "10-04"),
		#("houston", "san diego", "loss", "10-04"),
		("vancouver", "san jose", "win", "10-05"),
		("galaxy", "dallas", "win", "10-11"),
		("seattle", "salt lake", "win", "10-11"),
		("colorado", "lafc", "win", "10-18"),
		("san jose", "austin", "pending", "10-18"),
		("vancouver", "dallas", "win", "10-18"),
		("st louis", "salt lake", "win", "10-18"),
		#("kansas", "houston", "pending", "10-18"),
	]
	# pending_matches = [
	# 	("salt lake", "colorado", "win", "10-04"),
	# 	("dallas", "galaxy", "win", "10-04"),
	# 	#("houston", "san diego", "loss", "10-04"),
	# 	("vancouver", "san jose", "win", "10-05"),
	# 	("galaxy", "dallas", "pending", "10-11"),
	# 	("seattle", "salt lake", "pending", "10-11"),
	# 	("colorado", "lafc", "pending", "10-18"),
	# 	("san jose", "austin", "win", "10-18"),
	# 	("vancouver", "dallas", "pending", "10-18"),
	# 	("st louis", "salt lake", "pending", "10-18"),
	# 	#("kansas", "houston", "pending", "10-18"),
	# ]

	actual_pending_matches = []
	actual_current_points = current_teams.copy()
	for home, away, home_outcome, date in pending_matches:
		if home_outcome == "pending":
			actual_pending_matches.append((home, away))
		else:
			if home_outcome == "win":
				if home in actual_current_points:
					actual_current_points[home] += 3
			elif home_outcome == "loss":
				if away in actual_current_points:
					actual_current_points[away] += 3
			else:
				if home in actual_current_points:
					actual_current_points[home] += 1
				if away in actual_current_points:
					actual_current_points[away] += 1


	current_outcomes = []
	current_outcomes_old, possible_outcomes = add_all_outcomes(current_outcomes, actual_pending_matches)

	playoff_results = {}
	playoff_outcomes = {}
	possible_places = {}

	san_jose_in = 0
	for possible_outcome in possible_outcomes:
		outcome_points = actual_current_points.copy()
		for home, away, home_outcome in possible_outcome:
			if home_outcome == "win":
				if home in outcome_points:
					outcome_points[home] += 3
			elif home_outcome == "loss":
				if away in outcome_points:
					outcome_points[away] += 3
			else:
				if home in outcome_points:
					outcome_points[home] += 1
				if away in outcome_points:
					outcome_points[away] += 1

		sorted_outcome_points = sorted(outcome_points.items(), key=lambda x: x[1], reverse=True)
		place = 0
		for team, points in sorted_outcome_points:
			place += 1
			if team not in possible_places:
				possible_places[team] = set()
			possible_places[team].add(place)

		san_jose_top = False
		#print("--------")
		for team, points in sorted_outcome_points[:len(current_teams)-2]:
			if team == "san jose":
				san_jose_top = True
			#print(f"{team} : {points}")

		if san_jose_top:
			for home, away, home_outcome in possible_outcome:
				playoff_result = playoff_results.get((home, away))
				if playoff_result is None:
					playoff_results[(home, away)] = [home_outcome]
				elif home_outcome not in playoff_result:
					playoff_result.append(home_outcome)

				playoff_result = playoff_outcomes.get((home, away))
				if playoff_result is None:
					playoff_outcomes[(home, away)] = {home_outcome: [(possible_outcome, sorted_outcome_points)]}
				elif home_outcome not in playoff_result:
					playoff_result[home_outcome] = [(possible_outcome, sorted_outcome_points)]
				else:
					playoff_result[home_outcome].append((possible_outcome, sorted_outcome_points))

				if home_outcome == "win":
					if home in outcome_points:
						outcome_points[home] += 3
				elif home_outcome == "loss":
					if away in outcome_points:
						outcome_points[away] += 3
				else:
					if home in outcome_points:
						outcome_points[home] += 1
					if away in outcome_points:
						outcome_points[away] += 1

			san_jose_in += 1
			bldr = []
			for home, away, home_outcome in possible_outcome:
				if home_outcome == "win":
					bldr.append(f"{home} beats {away}")
				elif home_outcome == "loss":
					bldr.append(f"{away} beats {home}")
				else:
					bldr.append(f"{home} ties {away}")
			print(" | ".join(bldr))

			print(points_to_str(sorted_outcome_points))
			print("-" * 100)

	for (home, away), home_outcome_possible_outcomes in playoff_outcomes.items():
		for home_outcome, playoff_possible_outcomes in home_outcome_possible_outcomes.items():
			print("-" * 100)
			print(outcome_to_str(home, away, home_outcome))
			for possible_outcome, sorted_outcome_points in playoff_possible_outcomes:
				bldr = ["     "]
				for inner_home, inner_away, inner_home_outcome in possible_outcome:
					if inner_home == home and inner_away == inner_away:
						continue
					bldr.append(outcome_to_str(inner_home, inner_away, inner_home_outcome))
				bldr.append(" || ")
				bldr.append(points_to_str(sorted_outcome_points))
				print(" | ".join(bldr))

				#print(f"     {possible_outcome}")

	print(playoff_results)
	print(possible_places)


	#print(playoff_outcomes)


	# possible_outcomes = []
	# for home_score in range(0,5):
	# 	for away_score in range(0,5):
	# 		score_outcomes = []
	# 		for home, away in pending_matches:
	# 			score_outcomes.append((home, away, home_score, away_score))
	# 		possible_outcomes.append(score_outcomes)

	print(len(possible_outcomes))
	print(san_jose_in)