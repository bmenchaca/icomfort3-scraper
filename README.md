# icomfort3
PyPi library for accessing your Lennox S30, M30, and E30 thermostats via https://lennoxicomfort.com

Most of the information below is from the User Manual at: https://static.lennox.com/pdfs/owners/s30/Lennox_iComfortS30_Homeowner_Manual.pdf

# Overview
The heirachy of constructs in the Lennox Page looks like this:
  There may be one or more Homes,
  Which may contain one or more Lennox Climate Control systems (LCCs),
  Which may contain one or more Zones.
  
## Zones
  Each Zone contains a Mode, which is one of:
  * (Off, Cool Only, Heat Only, Heat/Cool)
    
  Each of these Modes contain required Temperatures, as:
  * (Off = None,
  *  Cool = Max Indoor Temp; >= Cooling Starts,
  *  Heat = Min Indoor Temp <= Heating Starts,
  *  Heat/Cool = Max and Min as above.  As a note, these cannot be closer than 3 degrees from each other.
  
  Additionally, each zone contains a Fan setting:
  *  On = Fan is turned on regardless of Climate Control,
  *  Auto = Fan is controlled by Climate Control,
  *  Circulate = As Auto, and also runs at a low rate between CC cycles.  The amount of time circulate runs per hour can be configured from the Settings->Fan->Circulate option (9 to 27 minutes).
  *  Allergen Defender = Circulates air inside when the air quality is bad outside to filter it.  This is basically Circulate mode that only runs if the Air Quality outside is poor.  For this to be an available option, Allergen Defender must be enabled in the Settings->Fan menu under Allergen Defender.
      
## Schedules
  The Mode and Fan settings can be automatically adjusted based on one or more Schedules.  These schedules change based on season: Summer, Winter, and Spring/Fall.  Each schedule is subdivided into Periods.  Each Period has a start time, as well as Mode and Fan settings.  Schedules can be configured to have the same Periods for all days of the week, different Periods for weekdays and weekends, or a different set of Periods every day.  For each configured day, there may be at most 4 periods.
        
  Schedule IQ has the same periods every day, and is based  wake-up time, sleep time, and away Mode scheduling rather than season or day of the week.
  
## Current Set Points (Mode)
  Instantaneous changes can be made to Mode, Temperatures, and Fan.  These will be automatically changed when the next schedule changes them, or a "Schedule Hold" can be set for a fixed amount of time to prevent the schedule from changing them.  The changes and the hold can be cancelled by disabling the Schedule Hold.
    
## Away Mode
  This mode may be set per household, and configures the Thermostat to put all LCCs and Zones into a cost-saving Heat/Cool setting.  The temperature for these may be controlled from the Settings->Away menu under away-set-points. You may also toggle Smart Away on, which uses the installed iComfort App on your phone to control automatic enabling of the Away feature using Geofencing for all participating devices.
