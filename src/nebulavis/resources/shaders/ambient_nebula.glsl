
#version 330
layout(std140) uniform BandData { float bands[256]; };
layout(std140) uniform FrameData { float frame[16]; };
uniform float uTime;
out vec4 fragColor;

float noise(vec3 p) {
return sin(p.x) * sin(p.y) * sin(p.z);
}

void main() {
vec2 uv = gl_FragCoord.xy / vec2(1920.0, 1080.0);
uv = uv * 2.0 - 1.0;
float bass = bands[2] * 1.5;
float t = uTime * 0.15 + bass;
float nebula = noise(vec3(uv * 1.8, t));
vec3 color = vec3(0.4 + nebula * 0.4, 0.2 + bass * 0.5, 0.6 + nebula * 0.3);
fragColor = vec4(color, 1.0);
}
