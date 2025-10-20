
#version 330
layout(std140) uniform BandData { float bands[256]; };
uniform float uTime;
out vec4 fragColor;

void main() {
vec2 uv = gl_FragCoord.xy / vec2(1920.0, 1080.0) - 0.5;
float angle = atan(uv.y, uv.x);
float radius = length(uv);
float bass = bands[5] * 2.0;
float tunnel = sin(10.0 * radius - uTime * (1.5 + bass));
float glow = smoothstep(0.5, 0.1, radius);
vec3 color = vec3(glow * (0.3 + bass), 0.1 + abs(tunnel) * 0.5, 0.6 + glow * 0.3);
fragColor = vec4(color, 1.0);
}
