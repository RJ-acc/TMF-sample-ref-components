'use strict';

//Minimal Service with filtering (equality match only) and attribute selection
//Error Handing Need to define a global error hqndler
//Paging and Range based Iterator to be added
//Notification to be added add listener and implement hub

const util = require('util');
const uuid = require('uuid');

const mongoUtils = require('../utils/mongoUtils');
const swaggerUtils = require('../utils/swaggerUtils');
const notificationUtils = require('../utils/notificationUtils');

const {sendDoc} = require('../utils/mongoUtils');

const {setBaseProperties, traverse, 
       addHref, processCommonAttributes } = require('../utils/operationsUtils');

const {validateRequest} = require('../utils/ruleUtils');

const {processAssignmentRules} = require('../utils/operations');

const {getPayloadType, getPayloadSchema, getResponseType} = require('../utils/swaggerUtils');

const {updateQueryServiceType, updatePayloadServiceType, cleanPayloadServiceType} = require('../utils/swaggerUtils');

const {TError, TErrorEnum, sendError} = require('../utils/errorUtils');

const MongoClient = require('mongodb').MongoClient;
const assert = require('assert');

exports.registerListener = function(req, res, next) {
  /**
   * Register a listener
   * Sets the communication endpoint address the service instance must use to deliver information about its health state, execution state, failures and metrics.
   *
   * data EventSubscriptionInput Data containing the callback endpoint to deliver the information
   * returns EventSubscription
   **/

  console.log('registerListener :: ' + req.method + ' ' + req.url + ' ' + req.headers.host);
  notificationUtils.register(req, res, next);  


};

exports.listListener = function(req, res, next) {
  /**
   * List or find Listener objects
   * This operation list or find Listener entities
   *
   * fields String Comma-separated properties to be provided in response (optional)
   * offset Integer Requested index for start of resources to be provided in response (optional)
   * limit Integer Requested number of resources to be provided in response (optional)
   * returns List
   **/

  console.log('listListener :: ' + req.method + ' ' + req.url + ' ' + req.headers.host);
  notificationUtils.index(req, res, next)

};

exports.unregisterListener = function(req, res, next) {
  /**
   * Unregister a listener
   * Resets the communication endpoint address the service instance must use to deliver information about its health state, execution state, failures and metrics.
   *
   * id String The id of the registered listener
   * no response value expected for this operation
   **/

  console.log('unregisterListener :: ' + req.method + ' ' + req.url + ' ' + req.headers.host);
  notificationUtils.unregister(req, res, next);  


};



