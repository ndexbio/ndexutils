var app = angular.module('myApp', ['ngRoute', 'ngDraggable']);

app.config(['$routeProvider',
    function ($routeProvider) {
        $routeProvider
        .when('/import-plan', {
            templateUrl: 'partials/importPlan.html',
            controller: 'myCtrl'
        })
        .otherwise({
            redirectTo: '/import-plan'
        });
    }]);


app.directive('fileReader', function() {
    return {
        scope: {
            fileReader:"=",
            csvSample:"=",
            fileHeader:"="
        },
        link: function(scope, element) {
            $(element).on('change', function(changeEvent) {
                var files = changeEvent.target.files;
                if (files.length) {
                    var r = new FileReader();
                    r.onload = function(e) {
                        var contents = e.target.result;
                        scope.$apply(function () {

                            var lines = contents.split('\n');
                            var returnArray = [];
                            for(var i = 0;i < lines.length;i++){
                                var tabbedData = [];
                                if(i <= 2){
                                    lineParsed = lines[i].split('\t');
                                    for(var j = 0;j < lineParsed.length;j++){
                                        tabbedData.push(lineParsed[j].replace(/(\r\n|\n|\r)/gm,""))
                                        if(i === 0){
                                            scope.fileHeader[j] = {title: lineParsed[j].replace(/(\r\n|\n|\r)/gm,""), selected: false}
                                        }
                                    }
                                    returnArray.push(tabbedData);
                                    console.log(lines[i]);
                                }
                            }
                            scope.csvSample = returnArray;

                            scope.fileReader = contents;
                        });
                    };

                  r.readAsText(files[0]);
                }
            });
        }
    };
});

