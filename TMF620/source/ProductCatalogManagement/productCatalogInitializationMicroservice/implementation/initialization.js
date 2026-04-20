const axios = require('axios');

var releaseName = process.env.RELEASE_NAME; 
var componentName = process.env.COMPONENT_NAME; 
const catalogApiBaseUrl = (process.env.CATALOG_API_BASE_URL ||
  'http://' + releaseName + '-productcatalogapi:8080/' + componentName + '/tmf-api/productCatalogManagement/v4').replace(/\/$/, '');

const metricsEventListner = {
  callback: process.env.METRICS_CALLBACK_URL || "http://" + componentName + "-sm:4000/listener"
}

const delay = ms => new Promise(res => setTimeout(res, ms));

const createMetricsEventListner = async () => {
  var complete = false;

  while (complete == false) {
    try {
        await delay(5000);  // retry every 5 seconds
        const url = catalogApiBaseUrl + '/hub';
        console.log('POSTing listner with callback ',metricsEventListner, ' to: ', url);
        const res = await axios.post(
          url, 
          metricsEventListner,
          {timeout: 10000});
        console.log(`Status: ${res.status}`);
        console.log('Body: ', res.data);
        complete = true;
        
        try {
          console.log('Telling Istio were finished');
          await axios.post(
            'http://127.0.0.1:15020/quitquitquit',
            {},
            {timeout: 10000});
        } catch (sidecarErr) {
          console.log('Istio sidecar quit endpoint unavailable; exiting successfully');
        }

        process.exit(0);
    } catch (err) {
      console.log('Initialization failed - retrying in 5 seconds');
    }
  }
};

createMetricsEventListner();
