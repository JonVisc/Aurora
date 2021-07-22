function toast_system_status(system_status_call)
{
    if(system_status_call["status"] == "ok")
    {
        if(system_status_call["message"])
        {
            create_snackbar("System Enabled Status",system_status_call["message"],"success")
        }
        else
        {
            create_snackbar("System Enabled Status","Successfully saved system config","success")
        }
    }
    

}

$('#aurora_extension_dropdown').on("change", function() { showExtensionDetails(this.value)})

