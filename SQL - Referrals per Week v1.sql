IF OBJECT_ID ('tempdb..#AvgWeeklyRefs') IS NOT NULL

	DROP TABLE #AvgWeeklyRefs

	CREATE TABLE #AvgWeeklyRefs

		(
		WeekNumber				int NULL
		,AvgRef					int NULL
		)

INSERT INTO #AvgWeeklyRefs

SELECT

	WeekNumber
	,AVG(Referrals) AS AvgRef

FROM

(SELECT
			
			
			Team = referral_team
			,DT.WeekCommencing
			,DT.WeekNumber
			,OptIn = CASE WHEN opt_in_date IS NULL THEN 'No' ELSE 'Yes' END
			,replicate('|',count(tr.treatment_id)) AS Chart
			,count(tr.treatment_id) AS Referrals
			--p.patient_id,
			--tr.episode_date_recieved
			
FROM 
	Stage1_IAPTUS.Extract.treatments tr 

	JOIN Stage1_IAPTUS.Extract.patients p 
		ON tr.patient_id = p.patient_id 
		AND p.duplicate = 0 
		AND p.dummy = 0	

	LEFT JOIN Informatics_SSAS_Live.dbo.DimDate DT
	ON cast(tr.episode_date_recieved as date) = DT.Date
		
 WHERE
	tr.live = 'yes'
	AND p.live = 'yes'
	AND tr.referral_team <> 'St. Helens Mindsmatter' -- exclude as no longer part of LSCFT
	AND DT.Date BETWEEN '2022-01-01' AND GETDATE()

GROUP BY referral_team, DT.WeekCommencing,DT.WeekNumber,CASE WHEN opt_in_date IS NULL THEN 'No' ELSE 'Yes' END) Sub

GROUP BY WeekNumber

ORDER BY WeekNumber asc

SELECT 

	WeekNumber
	,AvgRef
	,Mean = (SELECT AVG(AvgRef) FROM #AvgWeeklyRefs)
	,Variance = AvgRef - (SELECT AVG(AvgRef) FROM #AvgWeeklyRefs)
	,PCVar = ((AvgRef - (SELECT AVG(AvgRef) FROM #AvgWeeklyRefs))*1.0)/(SELECT AVG(AvgRef) FROM #AvgWeeklyRefs)

FROM #AvgWeeklyRefs