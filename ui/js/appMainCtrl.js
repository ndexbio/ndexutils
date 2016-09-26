var app = angular.module('myApp');

/*
==========================================================================================================
==========================================================================================================
==========================================================================================================
==========================================================================================================
==========================================================================================================
========================================= MAIN CONTROLLER ================================================
==========================================================================================================
==========================================================================================================
==========================================================================================================
==========================================================================================================
==========================================================================================================
*/

app.controller('myCtrl', function ($scope, $http, $window, $log, $filter, $location, $route, $timeout) {
    $scope.pythonHost = python_host_global; //use variable from env.js

    $scope.info = {
        message: "MAIN",
        fileHeader: {},
        sp: {source_plan: {}},
        tp: {target_plan: {}},
        ep: {edge_plan: {}},
        cp: {citation_plan: {}}
    };

    $scope.showMore = {
        sp: false,
        tp: false,
        ep: false,
        cp: false,
        export: false
    };

    $scope.contexts = [
        {tag: 'UniProt', selected: false},
        {tag: 'DrugBank', selected: false},
        {tag: 'Other', selected: false}
    ];

    $scope.contextURIs = [
        {tag: 'http://identifiers.org/uniprot/', selected: false},
        {tag: 'http://identifiers.org/drugbank/', selected: false},
        {tag: 'http://identifiers.org/other/', selected: false}
    ];


//    $scope.draggableObjects = [{name:'one'}, {name:'two'}, {name:'three'}];
//    $scope.droppedObjects1 = [];
//    $scope.droppedObjects2= [];
    $scope.onDropComplete1=function(data,evt, planType, planElementType){
        $scope.dragAndDropPlan(planType, planElementType, data)
        $scope.showMore.export = true;

        //var index = $scope.droppedObjects1.indexOf(data);
        //if (index == -1)
        //$scope.droppedObjects1.push(data);
    }

    $scope.clearBoxes = function() {
        $scope.info = {
            message: "MAIN",
            fileHeader: {},
            sp: {source_plan: {}},
            tp: {target_plan: {}},
            ep: {edge_plan: {}},
            cp: {citation_plan: {}}
        };

        $scope.showMore = {
            sp: false,
            tp: false,
            ep: false,
            cp: false,
            export: false
        };
    };

    $scope.setHeaderSelect = function(headerId){
        if(headerId in $scope.info.fileHeader){
            $scope.info.fileHeader[headerId].selected = !$scope.info.fileHeader[headerId].selected;
        }
    };

    $scope.clearSelectedHeader = function(){
        for (var key in $scope.info.fileHeader) {
           if ($scope.info.fileHeader.hasOwnProperty(key)) {
              $scope.info.fileHeader[key].selected = false;
           }
        }

        $scope.clearBoxes();
    };

    $scope.dragAndDropPlan = function(planType, planElementType, data){
        var planTypeObj = null;
        switch(planType) {
            case "SOURCE":
                planTypeObj = $scope.info.sp.source_plan;
                break;
            case "TARGET":
                planTypeObj = $scope.info.tp.target_plan;
                break;
            case "EDGE":
                planTypeObj = $scope.info.ep.edge_plan;
                break;
            case "CITATION":
                planTypeObj = $scope.info.cp.citation_plan;
                break;
            default:
                planTypeObj = $scope.info.sp.source_plan;
        }

        chooseFirstHeaderItem = false;
        if(planElementType != "property_columns"){
            chooseFirstHeaderItem = true;
        }

        //console.log(planTypeObj[planElementType]);
        if(chooseFirstHeaderItem){
            planTypeObj[planElementType] = data.title;
        } else {
            if (typeof planTypeObj[planElementType] != 'undefined') {
                if(planTypeObj[planElementType].indexOf(data.title) < 0){
                    planTypeObj[planElementType].push(data.title);
                }
            } else {
                planTypeObj[planElementType] =[data.title];
            }
        }
    };



    $scope.setPlan = function(planType, planElementType, data){
        var planTypeObj = null;
        switch(planType) {
            case "SOURCE":
                planTypeObj = $scope.info.sp.source_plan;
                break;
            case "TARGET":
                planTypeObj = $scope.info.tp.target_plan;
                break;
            case "EDGE":
                planTypeObj = $scope.info.ep.edge_plan;
                break;
            case "CITATION":
                planTypeObj = $scope.info.cp.citation_plan;
                break;
            default:
                planTypeObj = $scope.info.sp.source_plan;
        }

        chooseFirstHeaderItem = false;
        if(planElementType != "property_columns"){
            chooseFirstHeaderItem = true;
        }
        var addTheseItems = [];
        var headerItemFound = true;
        for (var key in $scope.info.fileHeader) {
            if ($scope.info.fileHeader.hasOwnProperty(key)) {
                if ($scope.info.fileHeader[key].selected) {
                    headerItemFound = true;
                    addTheseItems.push($scope.info.fileHeader[key].title);
                }
            }
        }

        if(!headerItemFound){
            addTheseItems.push(null);
        }

        if(chooseFirstHeaderItem){
            planTypeObj[planElementType] = addTheseItems[0];
        } else {
            planTypeObj[planElementType] = addTheseItems;
        }
    };

    $scope.exportPlan = function(){
        var returnJson = {
            source_plan: $scope.info.sp.source_plan,
            target_plan: $scope.info.tp.target_plan,
            edge_plan: $scope.info.ep.edge_plan,
            citation_plan: $scope.info.cp.citation_plan
        }

        var exportArrayString = "data:text/tsv;charset=utf-8,";

        exportArrayString += JSON.stringify(returnJson);

        var encodedUri = encodeURI(exportArrayString);

        window.open(encodedUri);

        console.log(returnJson);

    };

});
