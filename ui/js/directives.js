var app = angular.module('myApp');

app.directive('importPlanBuckets', function() {
    function link(scope, el, attrs) {
        scope.info = {
        }

        scope.onDropCompleteInner = function(parmData, parmEvent, planElementType){
            scope.onDropComplete({data: parmData, evt: parmEvent, planType: scope.planType, planElementType: planElementType});
            //console.log("In drop");
        };
    }
    return {
        scope: {
            planData:"=",
            planType:"=",
            onDropComplete:"&"
        },
        restrict: "EA",
        templateUrl: "partials/directives/importPlanBuckets.html",
        link: link
    };
});
