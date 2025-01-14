var focusflag = false;
var realname = "";
var email = "";
var containercount = 0;
var imagelist = [];

// 初始化加载

$(document).ready(function () {

    // alert("请注意，后端服务崩溃，无法进行调度作业！暂时不要申请作业，等到当前用户跑完，管理员会重启服务。");0.

    if ($.cookie("style") == "dark") {
        $("#csslink").attr("href", "/static/userPageNewDark.css");
    }
    uname = $.cookie("uname");
    if (uname == null) {
        window.location.href = "/login";
    }



    $.ajax({
        type: "GET",
        url: "/containermanager/imagelist",
        async: true,
        success: function (data) {
            imagelist = JSON.parse(data);
            for (var i = 0; i < imagelist.length; i++) {
                $(".image-selecter").append("<option>" + imagelist[i].imagename + "</option>");
            }
            $(".apply-for-container-form-dsc").find('p').text(imagelist[0].useguide);
            var env = ""

            for (var j = 0; j < imagelist[0].env.length; j++) {
                env += imagelist[0].env[j] + " ";
            }
            $(".apply-for-container-form-env").find('p').text(env)
        }
    });

    $.ajax({
        type: "GET",
        url: "/setting/loadname",
        async: true,
        success: function (data) {
            realname = data;
            $.cookie("realname", realname);
            $(".setting-form-body").find("input").first().val(data);

        }
    });

    $.ajax({
        type: "GET",
        url: "/setting/loademail",
        async: true,
        success: function (data) {
            email = data;
            $(".setting-form-body").find("input").eq(1).val(data);
        }
    });

   

    loadGPUInfo();
    loadMyContainers();
    loadWaitList();
    loadCurrItem();
    loadBackendStatus()
    setInterval(loadGPUInfo, 5 * 1000);
    setInterval(loadWaitList, 60 * 1000);
    setInterval(loadCurrItem, 60 * 1000);
    setInterval(loadBackendStatus, 60 * 1000);
});

// 初始化设置
$(function () {
    $(".apply-for-gpu-form-body").find("input").last().val("sh /home/" + $.cookie("uname") + "/workspace");
    // 删除10.16
    // $(".apply-for-gpu-form-body").find("input").eq(1).val("训练模型");
});

$(function () {
    $(".main-menu-btn").click(function () {
        if (focusflag) {
            $(".main-menu-btn").blur();
        } else {
            focusflag = true;
        }
    });
});


$(function () {
    $(".main-menu-btn").blur(function () { focusflag = false });
});

// 加载数据
function loadGPUInfo() {
    $.ajax({
        type: "GET",
        url: '/gpumanager/gpuinfo',
        async: true,
        success: function (data) {
            // new10.17
            var gpus = JSON.parse(data);
            for (var i = 0; i < gpus.length; i++) {
                var gpu = gpus[i];
                var memoryUsed = parseInt(gpu.memory.split("/")[0]);
                var memoryTotal = parseInt(gpu.memory.split("/")[1]);
                var memoryPercent = memoryUsed / memoryTotal;
                var progressId = "#gpu-progress-" + (i + 1);
                var labelId = "#gpu-label-" + (i + 1); // 假设你有对应的label标签
                var timeId = "#gpu-time-" + (i + 1);
                var waitId = "#gpu-wait-" + (i + 1);
                $(progressId).val(memoryPercent * 100);
                $(progressId).next("label").text(gpu.gputype + " - " + memoryUsed + "MB / " + memoryTotal + "MB");
                $(timeId).text("当前使用：" + gpu.currentuser);
                $(waitId).text("预计等待时间：" + gpu.waittime);
            }
            // end
//             var data = JSON.parse(data)[0];
//             var color_a = "white";
//             if ($("#csslink").attr("href") == "/static/userPageNew.css") {
//                 color_a = "black";
//             }
//             var memory = data.memory.split(" ")[0];
//             var memoryUsed = parseInt(memory.split("/")[0]);
//             var memoryTotal = parseInt(memory.split("/")[1]);
//             var memoryPercent = memoryUsed / memoryTotal;
//             var girth = 2 * Math.PI * 75;
//             $('#processbar').find("path").attr('stroke-dasharray', "" + girth * memoryPercent + " " + girth).css("stroke", getJetColor(memoryPercent));
//             $('#processbar').find("text").text(data.gputype).css("fill", color_a);

//             // show gpu info
//             $(".gpu-panel-info").children().eq(0).text("当前使用: " + data.currentuser);
//             $(".gpu-panel-info").children().eq(1).text("预计等待: " + data.waittime);
//             // 删除显存使用量显示 10.17
//             // $(".gpu-panel-memory").text("显存: " + data.memory);
//         }
//     });
// }
            // 如果需要显示整体GPU信息，确保数据结构正确
            if (gpus.length > 0) {
                var data = gpus[0]; // 使用数组的第一个元素
                var color_a = "white";
                if ($("#csslink").attr("href") == "/static/userPageNew.css") {
                    color_a = "black";
                }
                var memory = data.memory.split(" ")[0];
                var memoryUsed = parseInt(memory.split("/")[0].trim());
                var memoryTotal = parseInt(memory.split("/")[1].trim());
                var memoryPercent = memoryUsed / memoryTotal;
                var girth = 2 * Math.PI * 75;
                $('#processbar').find("path").attr('stroke-dasharray', "" + girth * memoryPercent + " " + girth).css("stroke", getJetColor(memoryPercent));
                $('#processbar').find("text").text(data.gputype).css("fill", color_a);

                // 显示整体GPU信息
                $(".gpu-panel-info").children().eq(0).text("当前使用: " + data.currentuser);
                $(".gpu-panel-info").children().eq(1).text("预计等待: " + data.waittime);
            }

        }
    });
}

function loadWaitList() {
    $.ajax({
        type: "GET",
        url: '/gpumanager/waitlist',
        success: function (data) {
            var data = JSON.parse(data);
            var table = $(".waitlist-tbody");
            table.children().remove();
            for (var i = 0; i < data.length; i++) {
                table.append("<tr><td>" + data[i].user + "</td><td>" + data[i].duration + "</td><td>" + data[i].reason + "</td></tr>");
            }
        }
    });
}

function loadMyContainers() {
    $.ajax({
        type: "GET",
        url: '/containermanager/mycontainer',
        success: function (data) {
            var data = JSON.parse(data);
            if (data.length == 0) {
                $(".mycontainers").hide();
                return;
            } else {
                $(".mycontainers").show();
            }
            if (containercount != data.length) {
                $(".containers-box").children().remove();
                containercount = data.length
            }
            var table = $(".containers-box");
            if (table.children().length == 0) {
                // 创建
                var temp = document.getElementById("container-card-template");
                for (var i = 0; i < data.length; i++) {
                    var newCard = $(temp.content.cloneNode(true));
                    table.append(newCard);
                }
                if (data.length > 1) {
                    table.children().eq(1).addClass("container-center");
                }
            }

            // 修改
            for (var i = 0; i < data.length; i++) {
                var Card = table.children().eq(i);
                Card.find(".container-name").text(data[i].containername);
                Card.find(".image-name").text(data[i].imagename);
                if (data[i].status == "running") {
                    Card.find(".container-status").find(".containe-status-flag").css("background-color", "green");
                    Card.find(".container-card-box2").css("visibility", "visible");
                    Card.find(".container-card-btn").first().text("\u2589").css("color", "red").append("<span class=\"container-card-btn-tip\">停止容器</span>");
                } else {
                    Card.find(".container-status").find(".containe-status-flag").css("background-color", "red");
                    Card.find(".container-card-box2").css("visibility", "hidden");
                    Card.find(".container-card-btn").first().text("▶").css("color", "green").append("<span class=\"container-card-btn-tip\">启动容器</span>");
                }

                Card.find(".container-status").find("p").text(data[i].status);
                var ports = data[i].ports;
                var ports = ports.split("|");
                var sshport = "";
                var jupyterport = "";
                var codeserverport = "";
                for (var j = 0; j < ports.length; j++) {
                    var port = ports[j].split("->");
                    if (port[0] == "22") {
                        var sshport = port[1];
                    }
                    if (port[0] == "8888") {
                        var jupyterport = port[1];
                    }
                    if (port[0] == "8080") {
                        var codeserverport = port[1];
                    }
                }
                Card.find(".container-card-box2").find("p").first().text("").append('<span class="info-tip">' + data[i].ports + '</span>' + data[i].ports);
                // Card.find(".container-card-box2").find("p").first().text(data[i].ports);

                if (sshport != "") {
                    Card.find(".container-card-box2").find("p").eq(1).text("").append('<span class="info-tip">' + "ssh -p " + sshport + " " + $.cookie("uname") + "@" + window.location.host.split(":")[0] + '</span>' + "ssh -p " + sshport + " " + $.cookie("uname") + "@" + window.location.host.split(":")[0]);
                }
                else {
                    Card.find(".container-card-box2").children().eq(1).hide();
                }
                if (jupyterport != "") {
                    Card.find(".container-card-box2").children().eq(2).find("a").text("http://" + window.location.host.split(":")[0] + ":" + jupyterport).attr("href", "http://" + window.location.host.split(":")[0] + ":" + jupyterport);
                }
                else {
                    Card.find(".container-card-box2").children().eq(2).hide();
                }
                if (codeserverport != "") {
                    Card.find(".container-card-box2").children().eq(3).find("a").text("http://" + window.location.host.split(":")[0] + ":" + codeserverport).attr("href", "http://" + window.location.host.split(":")[0] + ":" + codeserverport);
                }
                else {
                    Card.find(".container-card-box2").children().eq(3).hide();
                }
            }
        }
    });
}

function loadBackendStatus() {
     $.ajax({
        type: "GET",
        url: "/setting/backendstatus",
        async: true,
        success: function (data) {
            if (data == "true") {
                $(".backend").find("div").css("background-color", "green");
            } else {
                $(".backend").find("div").css("background-color", "red");
            }
        }
    });
}


// 处理单张卡
function loadCurrItem() {
    $.ajax({
        type: "GET",
        url: "/gpumanager/currentitem",
        async: true,
        success: function (data) {
            var data = JSON.parse(data);
            if (data.length == 0) {
                $(".curr-item").hide();
                return;
            }
            if (data[0].status == "正在使用") {
                // $(".curr-item").find('p').text("正在占用GPU:预计" + data[0].timeinfo);
                $(".cancel-gpu").text("提前结束");
            } else {
                // $(".curr-item").find('p').text("正在等待GPU:预计" + data[0].timeinfo);
                $(".cancel-gpu").text("取消申请");
            }
            $(".curr-item").show();
        }
    });
}
// new10.17 处理多卡
// function loadCurrItem() {
//     $.ajax({
//         type: "GET",
//         url: "/gpumanager/currentitem",
//         async: true,
//         success: function (data) {
//             var items = JSON.parse(data);
//             if (items.length === 0) {
//                 $(".curr-item").hide();
//                 return;
//             }

//             items.forEach(function(item) {
//                 var gpuIndex = item.gpuid;
//                 var cancelGpuButton = $("button.cancel-gpu[data-gpu-index='" + gpuIndex + "']");
                
//                 if (item.status === "正在使用") {
//                     cancelGpuButton.text("提前结束");
//                 } else {
//                     cancelGpuButton.text("取消申请");
//                 }
//             });

//             // 确保所有.curr-item都可见
//             $(".curr-item").show();
//         }
//     });
// }

// 容器操作
function startstopcontainer(event) {
    var containername = $(event.srcElement).parent().parent().parent().find(".container-name").text();
    var status = $(event.srcElement).text();
    if (status[0] == "▶") {
        var opt = "start";
    } else {
        var opt = "stop";
    }

    $.ajax({
        type: "POST",
        url: "/containermanager/containeropt",
        contentType: "application/json;charset=utf-8",
        data: JSON.stringify({ "containername": containername, "opt": opt }),
        success: function (data) {
            setTimeout(function () {
                loadMyContainers();
                if (!($(event.srcElement).text()[0] == "▶" ^ opt == "stop")) {
                    setTimeout(arguments.callee, 1000);
                } else {
                    $(".overlay").css("visibility", "hidden");
                }
            }, 1000);
        }
    });
    $(".overlay").first().css("visibility", "visible");
};

function deletecontainer(event) {

    var passwd = prompt("请输入密码:");

    if (passwd == "") {
        return;
    }
    $.ajax({
        type: "POST",
        url: "/checkpasswd",
        contentType: "application/json;charset=utf-8",
        data: JSON.stringify({ "password": passwd }),
        async: false,
        success: function (data) {
            if (data == "False") {
                $(".info-dialog").find("p").text("密码错误");
                $(".info-dialog").parent().css("visibility", "visible");
            } else {
                var containername = $(event.srcElement).parent().parent().parent().find(".container-name").text();
                containercount = $(".container-card").length;

                $.ajax({
                    type: "POST",
                    url: "/containermanager/containeropt",
                    contentType: "application/json;charset=utf-8",
                    data: JSON.stringify({ "containername": containername, "opt": "remove" }),
                    success: function (data) {
                        setTimeout(function () {
                            loadMyContainers();
                            if ($(".container-card").length != containercount) {
                                setTimeout(arguments.callee, 1000);
                            } else {
                                $(".overlay").css("visibility", "hidden");
                            }
                        }, 1000);
                    }
                });
                $(".overlay").first().css("visibility", "visible");
            }
        }
    })


};


// 设置菜单按钮
$(function () {
    $(".main-menu").children().first().click(function () {
        loadWaitList();
        var uname = $.cookie("uname");
        var waitlist = $(".waitlist").find("tbody").children();
        for (var i = 0; i < waitlist.length; i++) {
            if (waitlist.eq(i).children().first().text() == uname || waitlist.eq(i).children().first().text() == realname) {
                $(".info-dialog").find("p").text("您已经在等待列表中，请勿重复申请!");
                $(".info-dialog").parent().css("visibility", "visible");
                return;
            }
        }
         // 仅针对托管容器的下拉菜单进行操作
        var containerSelect = $(".container-selecter");
        
        containerSelect.children().remove(); // 移除所有现有选项
        containerSelect.append("<option value='' disabled selected>选择容器</option>"); // 添加默认提示选项
        var containers = $(".container-card");
        for (var i = 0; i < containers.length; i++) {
            if (containers.eq(i).find(".container-status").find("p").text() == "running") {
                containerSelect.append("<option>" + containers.eq(i).find(".container-name").text() + "</option>");
            }
        }
     $(".apply-for-gpu-form").parent().css("visibility", "visible");
    });

    $(".main-menu").children().eq(1).click(function () {
        if ($(".container-card").length == 3) {
            $(".info-dialog").find("p").text("每个人最多持有3个容器,请先删除一个容器之后再申请新的容器!");
            $(".info-dialog").parent().css("visibility", "visible");
            return;
        }
        $('.apply-for-container-form').parent().css("visibility", "visible");
    });

    $(".main-menu").children().eq(2).click(function () {
        $(".setting-form").parent().css("visibility", "visible");
    });

    $(".main-menu").children().eq(3).click(function () {
        $(".suggestion").parent().css("visibility", "visible");
    });

    $(".main-menu").children().eq(4).click(function () {
        window.location.href = "食用指北.html";
    });

    $(".main-menu").children().eq(5).click(function () {
        window.location.href = "/setting/quit";
    });
});

// new 10.17

// // 更新取消申请按钮的逻辑
// function updateCancelGpuButton() {
//   if (selectedGpuIndex !== null) {
//     const cancelGpuButton = document.querySelector('.cancel-gpu');
//     cancelGpuButton.dataset.gpuIndex = selectedGpuIndex;
//   }
// }
// end

// form表单提交
$(function () { // 申请GPU
    $(".apply-for-gpu-form-commit").click(function () {
        $(".overlay").css("visibility", "hidden");
        var uname = $.cookie("uname");
        var duration = $(".apply-for-gpu-form-body").find("input").first().val();
        // 获取选择的 GPU ID
        var selectedGpu = $(".gpu-select").val()
        localStorage.setItem("GpuId", selectedGpu);
        console.log(selectedGpu)
        var containername = $(".container-selecter").val();
        var reason = $(".apply-for-gpu-form-body").find("input").eq(1).val();
        var cmd = $(".apply-for-gpu-form-body").find("input").last().val();
        // 检查是否选择了不托管指令
        if (parseInt(duration) > 50) {
            $(".info-dialog").find("p").text("申请时间不可以大于50小时！");
            $(".info-dialog").parent().css("visibility", "visible");
            return; // 阻止申请提交
        }
        if (containername == "不托管指令") {
            containername = "";
            cmd = "";
            if (parseInt(duration) > 4) {
                $(".info-dialog").find("p").text("无指令最多申请4小时!");
                $(".info-dialog").parent().css("visibility", "visible");
                return;
            }
        }

        $.ajax({
            type: "POST",
            url: "/gpumanager/applyforgpu",
            contentType: "application/json;charset=utf-8",
            data: JSON.stringify({
                "gpuid": selectedGpu,
                "duration": duration,
                "reason": reason,
                "container": containername,
                "cmd": cmd
            }),
            success: function (data) {
                $(".info-dialog").find("p").text(data);
                $(".info-dialog").parent().css("visibility", "visible");
                loadWaitList();
                loadGPUInfo();
                loadCurrItem();
            }
        });

    });
});



$(function () { // 申请容器
    $(".apply-for-container-form-commit").click(function () {
        $(".overlay").css("visibility", "hidden");
        var imagename = $(".image-selecter").val();
        var ports = $(".apply-for-container-form-box2").find("input").first().val();
        containercount = $(".container-card").length;
        $.ajax({
            type: "POST",
            url: "/containermanager/applyforcontainer",
            contentType: "application/json;charset=utf-8",
            data: JSON.stringify({
                "imagename": imagename,
                "ports": ports
            }),
            success: function (data) {
                setTimeout(function () {
                    loadMyContainers();
                    if ($(".container-card").length != containercount) {
                        setTimeout(arguments.callee, 1000);
                    } else {
                        $(".overlay").css("visibility", "hidden");
                    }
                }, 1000);
            }
        });
        $(".overlay").first().css("visibility", "visible");
    });
});

$(function () { // 设置
    $(".setting-form-commit").click(function () {
        var newname = $(".setting-form-body").find("input").first().val();
        var newemail = $(".setting-form-body").find("input").eq(1).val();
        if (newname != realname) {
            $.ajax({
                type: "POST",
                url: "/setting/setname",
                contentType: "application/json;charset=utf-8",
                data: JSON.stringify({
                    "name": newname
                })
            });
            realname = newname;
        };
        if (newemail != email) {
            $.ajax({
                type: "POST",
                url: "/setting/setemail",
                contentType: "application/json;charset=utf-8",
                data: JSON.stringify({
                    "email": newemail
                })
            });
            email = newemail;
        };
        $(".overlay").css("visibility", "hidden");
    });
});

$(function () { // 意见反馈
    $(".suggestion-form-commit").click(function () {
        var suggestion = $(".suggestion-form-text").val();
        $.ajax({
            type: "POST",
            url: "/setting/suggest",
            contentType: "application/json;charset=utf-8",
            data: JSON.stringify({
                "content": suggestion
            })
        });
        $(".overlay").css("visibility", "hidden");
        $(".info-dialog").find("p").text("感谢您的反馈!");
        $(".info-dialog").parent().css("visibility", "visible");
        $(".suggestion-form-text").val("");
    });
});




// 其他函数\
// 实现的是单张显卡的
// $(function () {
//     $(".cancel-gpu").click(function () {
//         // var gpuIndex = $(this).data('data-gpu-index');
//         // // console.log( $(this).data);
//         // var gpuId = gpuIndex === undefined ? "0" : gpuIndex; 
//         var gpuIndex = $(this).data("gpu-index");
//         if (gpuIndex === undefined) {
//             alert("未选择GPU");
//             return;
//         }
//         if ($(this).text() == "取消申请") {
//             $.ajax({
//                 type: "POST",
//                 url: "/gpumanager/cancleapplyfor",
//                 contentType: "application/json;charset=utf-8",
//                 data: JSON.stringify({ "gpuid": gpuIndex }),
//                 success: function (data) {
//                     loadGPUInfo();
//                     loadWaitList();
//                     loadCurrItem();
//                 }
//             });
//         } else {
//             $.ajax({
//                 type: "POST",
//                 url: "/gpumanager/stopearlyweb",
//                 contentType: "application/json;charset=utf-8",
//                 data: JSON.stringify({ "gpuid": gpuIndex}),
//                 success: function (data) {
//                     loadGPUInfo();
//                     loadWaitList();
//                     loadCurrItem();
//                 }
//             });
//         };
//         loadGPUInfo();
//         loadWaitList();
//     });
// });


// function saveSelectedGpuIndex(index) {
//     selectedGpuIndex = index;
//     // 获取取消按钮
//     var cancelGpuButton = document.querySelector(".cancel-gpu");
//     // 设置 data-gpu-index 为选中的 GPU 值
//     cancelGpuButton.setAttribute("data-gpu-index", value);
// }

// 实现多卡
$(function () {
    $(".cancel-gpu").click(function () {
        // var gpuIndex = $(this).data('gpu-index'); // 获取绑定到按钮的数据gpu-index
        // var gpuIndex = $(".gpu-select").val()
        var selectedGpu = localStorage.getItem("GpuId");
        
        // var selectedGpu = $('data-gpu-index').val()
        // var selectedGpu = "1" // 测试用
        console.log(selectedGpu)

        var ajaxUrl = $(this).text() === "取消申请" ? "/gpumanager/cancleapplyfor" : "/gpumanager/stopearlyweb";
        
        $.ajax({
            type: "POST",
            url: ajaxUrl,
            contentType: "application/json;charset=utf-8",
            data: JSON.stringify({ "gpuid": selectedGpu}),
            success: function (data) {
                loadGPUInfo();
                loadWaitList();
                loadCurrItem();
            }
        });
    });
});


function getJetColor(percent) {
    percent = parseInt(percent * 255);
    if (percent < 32) {
        return "rgb(0,0," + (percent * 4 + 128) + ")";
    }
    else if (percent == 32) {
        return "rgb(0,0,255)";
    }
    else if (percent < 96) {
        return "rgb(0," + ((percent - 33) * 4 + 4) + ",255)";
    }
    else if (percent == 96) {
        return "rgb(2,255,254)";
    }
    else if (percent < 159) {
        return "rgb(" + (6 + (percent - 97) * 4) + ",255," + (250 - (percent - 97) * 4) + ")";
    }
    else if (percent == 159) {
        return "rgb(254,255,1)";
    }
    else if (percent < 224) {
        return "rgb(255," + (252 - (percent - 160) * 4) + ",0)";
    }
    else {
        return "rgb(" + (252 - (percent - 224) * 4) + ",0,0)";
    }
}

function closedialog() {
    $(".overlay").css("visibility", "hidden");
}

$(function () { // 镜像选择器
    $(".image-selecter").change(function () {
        var imagename = $(".image-selecter").val();
        for (var i = 0; i < imagelist.length; i++) {
            if (imagelist[i].imagename == imagename) {
                $(".apply-for-container-form-dsc").find('p').text(imagelist[i].useguide);
                var env = "";
                for (var j = 0; j < imagelist[i].env.length; j++) {
                    env += imagelist[i].env[j] + " ";
                }
                $(".apply-for-container-form-env").find('p').text(env)
                break;
            }
        }
    });
});

$(function () { //风格选择器
    $(".testswitch-checkbox").click(function () {
        if ($(this).prop("checked")) {
            $("#csslink").attr("href", "/static/userPageNewDark.css");
            $.cookie("style", "dark");
        }
        else {
            $("#csslink").attr("href", "/static/userPageNew.css");
            $.cookie("style", "light");
        };
        loadGPUInfo();
    });

    if ($.cookie("style") == "dark") {
        $(".testswitch-checkbox").click();
    }
});
