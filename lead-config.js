/*
  Where website booking requests are sent. The browser reads this file at page load.
  Edit it directly on GitHub (pencil icon), then commit. No rebuild is needed;
  allow up to about 10 minutes for browsers to pick up the change.

  use:  which endpoint is active, "dev" or "live". Leave as "" to disconnect; the form
        then tells visitors to phone in.
  key:  the X-Lead-Key Stefano sends you. The same key works for both Hub projects.
        It is visible to anyone who views the site source, so it is a spam filter, not a secret.
  emailBackupKey: optional web3forms.com access key, which also emails each lead to info@ldrservice.com.
*/
window.LS_LEADS = {
  use: "",
  endpoints: {
    dev:  "",   // https://<staging-ref>.supabase.co/functions/v1/website-lead
    live: ""    // https://<prod-ref>.supabase.co/functions/v1/website-lead
  },
  key: "",
  emailBackupKey: ""
};
