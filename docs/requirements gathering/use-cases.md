# Task 7.2 – Use Cases & Scenarios

Responsible: Ibrahim Mowafy
Phase: Requirements Gathering

## Use Case 1: Compare News Sources

Actor: BI User / Data Analyst

Preconditions:
- The Data Warehouse contains collected articles from at least two news websites.
- The user can open the dashboard.

Main Flow:
1. The user opens the dashboard.
2. The user selects "Source Comparison".
3. The user chooses a time period.
4. The system shows the number of articles per source and each source's share (%).
5. The user reviews the comparison.

Alternate Flow:
- A1: No articles exist for the chosen period. The system shows "No data available" and asks the user to choose another period.
- A2: Only one source has data. The system shows that source and a note that comparison is not possible.

Postconditions:
- The user has seen the article counts per source for the chosen period.
- No data in the Data Warehouse is changed.


## Use Case 2: Identify Shared News Stories

Actor: BI User / Data Analyst

Preconditions:
- The Data Warehouse contains articles from at least two news websites.
- Articles about the same or similar stories have already been grouped by the system.
- The user can open the dashboard.

Main Flow:
1. The user opens the dashboard.
2. The user selects "Shared Stories".
3. The user chooses a time period.
4. The system shows the stories that were covered by more than one source.
5. For each story, the system shows how many sources covered it and their names.
6. The user selects one story to see its articles from each source.

Alternate Flow:
- A1: No story was covered by more than one source in the chosen period. The system shows "No shared stories found".
- A2: Story grouping data is not available. The system shows an error message and asks the user to try again later.

Postconditions:
- The user has seen the list of shared stories and the number of sources for each one.
- No data in the Data Warehouse is changed.


## Use Case 3: Compare Publication Times

Actor: BI User / Data Analyst

Preconditions:
- The Data Warehouse contains articles with publication date and time from at least two news websites.
- Articles about the same story have already been grouped by the system.
- The user can open the dashboard.

Main Flow:
1. The user opens the dashboard.
2. The user selects "Publication Time Comparison".
3. The user selects a story that was covered by more than one source.
4. The system shows the publication date and time for each source, from earliest to latest.
5. The system shows the time difference between the first source and each of the others.
6. The user reviews the differences.

Alternate Flow:
- A1: The selected story was published by only one source. The system shows a note that comparison is not possible.
- A2: One article has no publication time. The system shows "Time not available" for that source and compares the others.

Postconditions:
- The user has seen when each source published the story and the time differences between them.
- No data in the Data Warehouse is changed.


## Use Case 4: Monitor Pipeline Execution

Actors: System Administrator / Project Team Member (primary), Scheduler (supporting)

Preconditions:
- The Scheduler is set up to run the scraping and data-processing jobs automatically.
- At least one pipeline run has been recorded in the execution logs.
- The administrator can open the monitoring page.

Main Flow:
1. The Scheduler starts a scraping and data-processing run at the scheduled time.
2. The system records the result of the run (success or failure) in the execution log.
3. The administrator opens the monitoring page.
4. The system shows the latest runs with their status and time.
5. The system shows the Pipeline Success Rate (%) and the Scraping Failure Rate (%).
6. The administrator selects a failed run to see the error details.

Alternate Flow:
- A1: No runs are recorded yet. The system shows "No pipeline runs found".
- A2: A news website is not reachable during a run. The system marks that source as failed, continues with the other sources, and records the error in the log.

Postconditions:
- The administrator knows which runs succeeded and which failed, and why.
- Every run result is saved in the execution log.


## Use Case 5: Maintain Data Quality

Actors: System Administrator / Project Team Member (primary), Scheduler (supporting)

Preconditions:
- Articles have been collected from the news websites.
- The Scheduler is set up to run the data-processing jobs automatically.

Main Flow:
1. The Scheduler starts the data-processing job.
2. The system checks that each article has the required fields (title, source, link, and publication date).
3. The system standardizes the data, for example the date format and the source names.
4. The system finds duplicate articles and keeps only one copy.
5. The system stores the clean articles in the Data Warehouse.
6. The administrator opens the data quality page.
7. The system shows the Data Completeness (%) and the Duplicate Article Rate (%).

Alternate Flow:
- A1: An article is missing a required field. The system does not store it, and records it in the log with the reason.
- A2: An article is a duplicate. The system does not store it again, and counts it in the Duplicate Article Rate.

Postconditions:
- The Data Warehouse contains only checked and standardized articles.
- The administrator can see how complete and clean the data is.
