# Wekiva State College and Central Florida Atlantic University

This folder is a GUIDE v1.0.0 extract for two fictional Central Florida institutions
in one consortium. The people, courses, and amounts are fictional.

## Files

- `csv/` and `parquet/` hold the same rows. Parquet is the easier file to query.
  An object is included only when the extract has rows for it. Objects nothing
  references are left out. The schema file still describes the full GUIDE model.
- `manifest.json` records the as-of date, the operational window, the time zone,
  the two organization identifiers, and the names of the omitted objects.

## How the rows join

People are `PersonIdentifier`. Organizations are `college` and `university`.
A term is `TermIdentifier`, a course is `CourseIdentifier`, and a section is
`ClassIdentifier`. Enrollment joins a person to a section. A grade is
`EnrollmentAcademicOutcome`, joined on `EnrollmentIdentifier`.

Grades from a term that begins before the window in `manifest.json` are
transcript history. The outcome is present and `EnrollmentIdentifier` is
empty. Sections, alerts, appointments, aid, and course-site events begin
at the window. Terms, catalogs, and programs can start earlier.

Terms that begin after the as-of date are published so a degree plan can name
them. Those terms do not have sections or registrations yet.

Degree progress joins `PersonProgram` to `PersonProgramProgressEvaluation`,
then to `PersonProgramRequirementEvaluation`, then to
`PersonProgramRequirementEvidence`, then to `LearnerAcademicCredit`.

A degree plan joins `LearnerDegreePlan` to `LearnerDegreePlanItem` on
`LearnerDegreePlanIdentifier` and on `RevisionIdentifier` =
`LearnerDegreePlanRevisionIdentifier`. The item then joins
`ProgramRequirement`, `CourseLookup`, and `TermLookup`.

## Soft delete and as-of

`DeletedDate` marks a row the school removed. Queries that want the current
file should keep rows whose `DeletedDate` is empty. `CreatedDate` and
`UpdatedDate` are on or before the as-of date. A term can still begin after
that date; those are the planning terms above, and they have no sections.

`CreatedBy`, `UpdatedBy`, and `DeletedBy` are staff account numbers from
1000 through 9999. They are not person identifiers.

## Scores

`PredictedProbability` is the chance of the model's `TargetOutcome`.
In this extract the college model targets persistence and the university
model targets retention. A higher value means the model considers that
outcome more likely. `PredictionCategory` is a bucket of that probability.
`ScoreValue` is the same probability on a 0 to 100 scale.

## Starter queries

```sql
SELECT "Name" FROM read_parquet('parquet/Organization.parquet');

SELECT "FirstName", "LastOrSurname"
FROM read_parquet('parquet/PersonLookup.parquet')
WHERE "DeletedDate" IS NULL
LIMIT 20;

SELECT e."PersonIdentifier", c."Name", e."Status"
FROM read_parquet('parquet/Enrollment.parquet') e
JOIN read_parquet('parquet/ClassLookup.parquet') c
  ON c."ClassIdentifier" = e."ClassIdentifier"
LIMIT 20;

SELECT "PersonIdentifier", "PredictedProbability", "PredictionCategory"
FROM read_parquet('parquet/LearnerSuccessPrediction.parquet')
WHERE "DeletedDate" IS NULL
LIMIT 20;

SELECT "Code", "BeginDate", "EndDate"
FROM read_parquet('parquet/TermLookup.parquet')
ORDER BY "BeginDate";

SELECT p."PersonIdentifier", e."EvaluationDateTime", e."TotalCreditsApplied",
       e."RequirementsSatisfiedIndicator"
FROM read_parquet('parquet/PersonProgramProgressEvaluation.parquet') e
JOIN read_parquet('parquet/PersonProgram.parquet') p
  ON p."PersonProgramIdentifier" = e."PersonProgramIdentifier"
WHERE e."DeletedDate" IS NULL
QUALIFY row_number() OVER (
  PARTITION BY e."PersonProgramIdentifier"
  ORDER BY e."EvaluationDateTime" DESC
) = 1;

SELECT "FinancialAidAwardType", count(*) AS awards
FROM read_parquet('parquet/LearnerFinancialAidAward.parquet')
GROUP BY 1
ORDER BY 2 DESC;

SELECT "AttendanceStatus", count(*) AS meetings
FROM read_parquet('parquet/LearnerClassAttendance.parquet')
GROUP BY 1;

SELECT "Action", count(*) AS events
FROM read_parquet('parquet/StreamedEvent.parquet')
GROUP BY 1
ORDER BY 2 DESC
LIMIT 10;
```
