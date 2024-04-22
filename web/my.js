function to_percent(value) {
    if (typeof value === 'number' && !isNaN(value)) {
        return (value * 100).toFixed(2) + '%'; // toFixed() 函数保留两位小数并返回字符串形式的结果
    } else {
        return value;
    }
}
my_vue = new Vue({
    el: '#app',
    data: {
        paths: [],
        model_result_in_progress : false,
        model_result_req : {
            min_certainly : 0,
            path: '',
            topk: 4,
            dedup: true
        },
        model_result_rsp: [],
        model_result_show_idx : 0
    },
    mounted() {
        axios.get('/model_list')
            .then(response => {
                this.paths = response.data;
                if (this.paths.length > 0 ){
                    this.model_result_req.path = this.paths[0];
                }
                
            })
            .catch(error => {
                console.error('There was an error!', error);
            });
        
    },
    watch: {
        // 当model_result_rsp变化时自动调用updateCharts方法
        model_result_rsp: {
            handler: 'updateCharts',
            deep: true // 深度监听，监听内部属性的变化
        }
    },
    methods: {
        post_call(func, data, callback) {
            return axios.post(`/${func}`, data)
                .then(response => {
                    console.log(response)
                    callback(response)
                    return response.data;
                })
                .catch(error => {
                    console.error('There was an error:', error);
                }); 
        },
        fetchModelResult() {
            if (!this.model_result_req.path) return;
            function parse_rsp(response) {
                my_vue.model_result_rsp = response.data
                my_vue.model_result_in_progress = false;
            }
            my_vue.model_result_in_progress = true;
            this.post_call('model_result_process', this.model_result_req, parse_rsp);
        },
        mergeModelResult() {
            if (!this.model_result_req.path) return;
            function parse_rsp(response) {
                alert(response.data); 
                my_vue.model_result_in_progress = false;
            }
            my_vue.model_result_in_progress = true;
            this.post_call('merge_results', {'path' : this.model_result_req.path}, parse_rsp);
        },
        updateCharts() {
            this.$nextTick(() => {
                this.model_result_rsp.forEach((result, index) => {
                    this.createChart(result, index);
                });
            });
        },
        createChart(single_rsp, index) {
            console.log("生成date-return折线图: " + index)
            console.log(single_rsp)
            
            Highcharts.chart('line-chart-' + index, {
                chart: {
                    type: 'line'
                },
                title: {
                    text: '回测: 每天的收益'
                },
                xAxis: {
                    categories: single_rsp.days
                },
                yAxis: {
                    title: {
                        text: 'Return'
                    }
                },
                series: [
                    {
                        name: '回测收益',
                        data: single_rsp.return_per_day,
                        visible: false
                    },
                    {
                        name: '模型rank(/10万)',
                        data: single_rsp.rank_per_day.map(item => item/100000),
                        visible: false
                    },
                    {
                        name: '模型预估收益',
                        data: single_rsp.pred_per_day
                    }
                ],
            });
            data = single_rsp.classify
            if (data.length > 8) {
                data = data.slice(0, 8)
            }
            
            // 提取 categories
            const categories = data.map(item => item.category);
            
            // 提取 count 数据
            const countData = data.map(item => item.count);
            
            // 提取 stock_size 数据
            const stockSizeData = data.map(item => item.stock_size);
            
            // 提取 stock_size 数据
            const tokp_avg_pred = data.map(item => item.tokp_avg_pred);
            
            // Highcharts 配置
            Highcharts.chart('classify-chart-' +index, {
                chart: {
                    type: 'column'
                },
                title: {
                    text: '分类板块统计'
                },
                xAxis: {
                    categories: categories,
                    crosshair: true
                },
                yAxis: {
                    min: 0,
                    title: {
                        text: '数量'
                    }
                },
                tooltip: {
                    shared: true
                },
                plotOptions: {
                    column: {
                        pointPadding: 0.1,
                        borderWidth: 0
                    }
                },
                series: [{
                    name: 'count',
                    data: countData,
                    color: 'rgba(0, 148, 255, 0.75)', // 示例颜色，可根据需要修改,
                    visible: false
                }, {
                    name: 'stock_size',
                    data: stockSizeData,
                    color: 'rgba(255, 99, 71, 0.75)', // 示例颜色，可根据需要修改,
                    visible: false
                }, {
                    name: 'tokp_avg_pred',
                    data: tokp_avg_pred,
                    color: 'rgba(255, 159, 64, 0.75)' // 示例颜色，可根据需要修改
                }]
            });
        }

    }
});