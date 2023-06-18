# Microbehaviors

## Introduction
We need to send client users reports of their microbehavior statistics when using the app. We also
need to send an aggregated report to HR.
The strategy is to
- generate these microbehavior reports at predetermined time-intervals using `cron`.
- `cron` will call the management commands to generate these reports. 
- meanwhile `cron` will also call management commands to make the computations, and store them in the database.
- Since the code won't know how often they are called, we'll need to put the interval in a config file.
- The database table will still be defined in Upshot-backend. This project and this app will contain the codes to generate
the data and the reports.