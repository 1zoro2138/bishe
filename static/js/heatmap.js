function initHeatmap(data) {
    var myChart = echarts.init(document.getElementById('heatmap'));

    var option = {
        title: { text: '全国票房热力图' },
        tooltip: {
            trigger: 'item'
        },
        visualMap: {
            min: 0,
            max: Math.max(...Object.values(data)),
            left: 'left',
            top: 'bottom',
            text: ['高', '低'],
            calculable: true
        },
        series: [{
            name: '票房',
            type: 'map',
            map: 'china', // 与 china.js 中的地图名称一致
            roam: true,
            label: {
                show: true
            },
            data: Object.entries(data).map(([name, value]) => ({ name, value }))
        }]
    };
    myChart.setOption(option);

    // 点击跳转到省份分析详情
    myChart.on('click', function (params) {
        if (params.name) {
            // 提取省份基础名称，去掉"省"、"市"、"自治区"等后缀
            let baseName = params.name;
            baseName = baseName.replace(/(省|市|自治区|维吾尔|回族|壮族)$/g, '');
            
            // 特殊处理内蒙古自治区
            if (params.name === '内蒙古自治区') {
                baseName = '内蒙古';
            }
            
            window.location.href = '/province_analysis/' + baseName;
        }
    });
}
