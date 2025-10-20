
#version 330
layout(std140) uniform BandData { float bands[256]; };
layout(std140) uniform FrameData { float frame[16]; };
uniform float uTime;
out vec4 fragColor;

float height(vec2 pos) {
float bass = bands[3];
return sin(pos.x * 2.0 + uTime * 0.3) * cos(pos.y * 3.0 - uTime * 0.2) * (0.2 + bass);
}

void main() {
vec2 uv = gl_FragCoord.xy / vec2(1920.0, 1080.0);
vec2 pos = uv * 4.0;
float h = height(pos);
vec3 color = mix(vec3(0.1, 0.08, 0.2), vec3(0.8, 0.5, 0.2), h + 0.5);
fragColor = vec4(color, 1.0);
}
