let sw = 0;

window.onbeforeunload = async function(e){
    await eel.close()();
}

const compile = async function(e){
    const ret = await eel.compile(editor.getValue())();
    const success = await eel.success()();
    if (success) {
        message.style.color="#CCCCCC";
        message.innerHTML ="shader compile succeeded";
    } else {
        message.style.color="#FF8866";
        message.innerHTML =ret;
    }
    return success;
}

const play = async function(e){await eel.play()();}
const stop = async function(e){await eel.stop()();}
const intervalSet  = async function(e){
    await eel.startTime(Number(start.value))()
    await eel.endTime(Number(end.value))()
}

btnSw.onclick = function(e){
    if (sw === 0) {
        const flag = compile();
        if (flag){
            intervalSet();
            play();
            sw = 1;
            btnSw.innerHTML = "STOP";
            start.disabled = true;
            end.disabled = true;
        } 
    } else {
        stop();
        sw = 0;
        btnSw.innerHTML = "PLAY";
        start.disabled = false;
        end.disabled = false;
    }
    editor.focus();
};

reset.onclick = async function(e){
    await eel.reset()()
}

const reList=function(dom, list, head){
    while(dom.lastChild){
		dom.removeChild(dom.lastChild);
	}
    if(head.length>0){
        const op = document.createElement("option");
        op.text = head;
        op.value = "";
        dom.appendChild(op);
    }
    for(let i=0;i<list.length;i++){
        if(list[i].length>0){
            const op = document.createElement("option");
            op.text = list[i];
            op.value = list[i];
            dom.appendChild(op);
        }
    }
};

const editor = ace.edit("editor");
editor.session.setUseWrapMode(true);
editor.setTheme("ace/theme/tomorrow_night_blue");
//editor.setTheme("ace/theme/chaos");
//editor.setTheme("ace/theme/twilight");
editor.getSession().setMode("ace/mode/glsl");
editor.setShowFoldWidgets(true);
editor.setOptions({
    fontSize: "10pt"
});
editor.session.on("change", async function(){
    //shadertoy measures
    if (editor.getValue().match(/mainSound.*(.*int.*,.*float.*)/)==null){
        editor.setValue(editor.getValue().replace(/mainSound.*float/,'mainSound(int samp, float'));
    }
    char.innerHTML = await eel.charSize(editor.getValue())() + ' chars';
    if(sw==1){
        const flag = await compile();
        if(flag){
            await eel.saveShader(categoryList.value, shaderList.value, editor.getValue())();
        }
    }
});

const setText = function(src){
    editor.setValue(src);
    editor.focus();
    editor.gotoLine(1);
    editor.gotoPageUp();
};

eel.expose(time);
function time(t){
    counter.innerHTML =("00"+Math.floor(t/60)).substr(-2)+":"+("00"+(t%60).toFixed(1)).substr(-4);
};

categoryList.onchange = async function(e){
    let a = await eel.listShaders(categoryList.value)();
    a = a.split(",");
    reList(shaderList, a, "");
    shaderList.selectedIndex = 0;
    const src = await eel.loadShader(categoryList.value,shaderList.value)();
    setText(src);
};

shaderList.onchange = async function(e){
    const src = await eel.loadShader(categoryList.value,shaderList.value)();
    setText(src);
};

shiftList.onchange = async function(e){
    const next = shiftList.value
    const name = await eel.shiftShader(
        categoryList.value,
        next,
        shaderList.value)();
    let a = await eel.listCategory()();
    a = a.split(",");
    reList(categoryList, a, "");
    categoryList.selectedIndex = a.indexOf(next)
    reList(shiftList, a, "-- select category --");
    shiftList.selectedIndex = 0;
    a = await eel.listShaders(categoryList.value)();
    a = a.split(",");
    reList(shaderList, a, "");
    shaderList.selectedIndex = a.indexOf(name);
};

shaderNew.onclick = async function(e){
    name = await eel.newShader(categoryList.value)();
    a = await eel.listShaders(categoryList.value)();
    a = a.split(",");
    reList(shaderList, a, "");
    shaderList.selectedIndex = a.indexOf(name);
    shaderList.onchange();
};

shaderFork.onclick = async function(e){
    const name = await eel.forkShader(categoryList.value, shaderList.value)();
    let a = await eel.listShaders(categoryList.value)();
    a = a.split(",");
    reList(shaderList, a, "");
    shaderList.selectedIndex = a.indexOf(name);
};

categoryNew.onclose = async function(e){
    const ret = this.returnValue;
    if(ret=="") return;
    const flag = await eel.newCategory(ret)();
    if(flag == 0){
        badName.showModal();
    }else{
        let a = await eel.listCategory()();
        a = a.split(",");
        reList(categoryList, a, "");
        reList(shiftList, a, "-- select category --");
        categoryList.selectedIndex = a.indexOf(ret);
        a = await eel.listShaders(categoryList.value)();
        a = a.split(",");
        reList(shaderList, a, "");
        shaderList.selectedIndex = 0;
        const src = await eel.loadShader(categoryList.value,shaderList.value)();
        setText(src);
    }
}

categoryRename.onclose = async function(e){
    const ret = this.returnValue;
    if(ret=="") return;
    if(ret==categoryList.value) return;
    const flag = await eel.renameCategory(categoryList.value, ret)();
    if(flag == 0){
        badName.showModal();
    }else{
        let a = await eel.listCategory()();
        a = a.split(",");
        reList(categoryList, a, "");
    }
}

shaderRename.onclose = async function(e){
    const ret = this.returnValue;
    if(ret=="") return;
    if(ret==shaderList.value) return;
    const flag = await eel.renameShader(categoryList.value, shaderList.value, ret)();
    if(flag == 0){
        badName.showModal();
    }else{
        a = await eel.listShaders(categoryList.value)();
        a = a.split(",");
        reList(shaderList, a, "");
        shaderList.selectedIndex = 0;
        shaderList.selectedIndex = a.indexOf(ret);
    }
}

shaderDel.onclose = async function(e){
    const ret = this.returnValue;
    if(ret==0)return;
    const flag = await eel.delShader(categoryList.value,shaderList.value)();
    if(flag == 1){
        let a = await eel.listCategory()();
        a = a.split(",");
        reList(categoryList, a, "");
    }
    let a = await eel.listShaders(categoryList.value)();
    a = a.split(",");
    reList(shaderList, a, "");
    const src = await eel.loadShader(categoryList.value,shaderList.value)();
    setText(src);
};

download.onclick = function(){
  text = editor.getValue();
  let blob = new Blob([text]);
  let a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.target = "_blank";
  a.download = "sound.glsl";
  a.click();
};

(async function(){
    let a = await eel.listCategory()();
    a = a.split(",");
    reList(categoryList, a, "");
    reList(shiftList, a, "-- select category --");
    a = await eel.listShaders(categoryList.value)();
    a = a.split(",");
    reList(shaderList, a, "");
    const src = await eel.loadShader(categoryList.value,shaderList.value)();
    setText(src);
})();

const gl = canvas.getContext("webgl2") || canvas.getContext("experimental-webgl2");
let p = gl.createProgram();
let sh = gl.createShader(gl.VERTEX_SHADER);
gl.clearColor(0.1,0.1,0.1,1);
gl.shaderSource(sh, 
`#version 300 es
layout(location=0) in float gain;
uniform float chunk;
void main(){
    float id = float(gl_VertexID);
    float x =mod(id,chunk)/chunk-0.5;
    float y =floor(id/chunk)-0.5;
    gl_Position = vec4(x*1.8, y*0.1+gain*0.8, 0,1);
}
`);
gl.compileShader(sh);
gl.attachShader(p, sh);
gl.deleteShader(sh);
sh = gl.createShader(gl.FRAGMENT_SHADER);
gl.shaderSource(sh, 
`#version 300 es
precision highp float;
uniform vec3 col;
out vec4 fragColor;
void main(){
  fragColor  = vec4(col,1);
}
`
);
gl.compileShader(sh);
gl.attachShader(p, sh);
gl.deleteShader(sh);
gl.linkProgram(p);
gl.useProgram(p);

const chunk = 1024;

gl.uniform1f(gl.getUniformLocation(p, "chunk"), chunk);

let vbo = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
gl.enableVertexAttribArray(0);
gl.vertexAttribPointer(0, 1,gl.FLOAT, false, 0, 0);    

eel.expose(data);
function data(d){
    //console.log(d.length)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(d), gl.DYNAMIC_COPY);
};

(function () { 
    requestAnimationFrame(arguments.callee);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.uniform3f(gl.getUniformLocation(p, "col"), .7,.6,.5);
    gl.drawArrays(gl.LINE_STRIP, 0, chunk);
    gl.uniform3f(gl.getUniformLocation(p, "col"), .5,.6,.7);
    gl.drawArrays(gl.LINE_STRIP, chunk, chunk);
})();
